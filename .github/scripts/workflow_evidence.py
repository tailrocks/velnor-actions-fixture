#!/usr/bin/env python3
"""Repository-local payload and semantic evidence comparator for fixtures."""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path
from typing import Any


IDENTITY_FIELDS = frozenset(
    {"lane", "runner", "runner_name", "run_id", "job_id", "observed_at"}
)


def normalize(value: Any) -> Any:
    """Normalize JSON object ordering and remove runner-only identity fields."""
    if isinstance(value, dict):
        return {
            key: normalize(item)
            for key, item in sorted(value.items())
            if key not in IDENTITY_FIELDS
        }
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def differing_paths(left: Any, right: Any, path: str = "$") -> list[str]:
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        differences: list[str] = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                differences.append(f"{path}.{key}")
            else:
                differences.extend(differing_paths(left[key], right[key], f"{path}.{key}"))
        return differences
    if isinstance(left, list):
        if len(left) != len(right):
            return [path]
        differences = []
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            differences.extend(differing_paths(left_item, right_item, f"{path}[{index}]"))
        return differences
    return [] if left == right else [path]


def load_evidence(directory: Path, scenario: str, lanes: set[str]) -> dict[tuple[str, str], dict[str, Any]]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    expected_schema = {
        "docker-lease-probe": "velnor.fixture.docker-lease-probe.v1",
        "success": "velnor.fixture.control-plane.v1",
        "failure": "velnor.fixture.control-plane.v1",
        "hold": "velnor.fixture.control-plane.v1",
        "concurrent": "velnor.fixture.control-plane.v1",
        "artifacts": "velnor.fixture.control-plane.v1",
        "cache": "velnor.fixture.control-plane.v1",
        "load": "velnor.fixture.control-plane.v1",
    }.get(scenario)
    for path in sorted(directory.rglob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SystemExit(f"invalid evidence {path}: {error}") from error
        if not isinstance(record, dict):
            raise SystemExit(f"invalid evidence {path}: root must be an object")
        if record.get("scenario") != scenario:
            raise SystemExit(
                f"unexpected scenario in {path.relative_to(directory)}: "
                f"{record.get('scenario')!r}, expected {scenario!r}"
            )
        if expected_schema is not None and record.get("schema") != expected_schema:
            raise SystemExit(
                f"unexpected evidence schema in {path.relative_to(directory)}: "
                f"{record.get('schema')!r}, expected {expected_schema!r}"
            )
        lane = record.get("lane")
        evidence_id = record.get("evidence_id", "default")
        if lane not in lanes:
            raise SystemExit(f"unexpected evidence lane in {path.relative_to(directory)}: {lane!r}")
        if not isinstance(evidence_id, str) or not evidence_id:
            raise SystemExit(f"invalid evidence_id in {path.relative_to(directory)}")
        if not isinstance(record.get("semantic"), (dict, list)):
            raise SystemExit(f"missing semantic evidence in {path.relative_to(directory)}")
        key = (lane, evidence_id)
        if key in records:
            raise SystemExit(f"duplicate evidence for {lane}/{evidence_id}")
        records[key] = record

    if not records:
        raise SystemExit(f"no evidence found in {directory}")
    observed_lanes = {lane for lane, _ in records}
    if observed_lanes != lanes:
        raise SystemExit(
            f"lane evidence mismatch: expected {sorted(lanes)}, got {sorted(observed_lanes)}"
        )
    ids_by_lane = {lane: {item_id for item_lane, item_id in records if item_lane == lane} for lane in lanes}
    expected_ids = next(iter(ids_by_lane.values()))
    for lane, evidence_ids in ids_by_lane.items():
        if evidence_ids != expected_ids:
            raise SystemExit(
                f"evidence id mismatch for {lane}: expected {sorted(expected_ids)}, "
                f"got {sorted(evidence_ids)}"
            )
    return records


def compare(args: argparse.Namespace) -> int:
    lanes = set(args.lanes)
    records = load_evidence(Path(args.directory), args.scenario, lanes)
    evidence_ids = sorted({evidence_id for _, evidence_id in records})
    if len(lanes) == 1:
        print(
            f"{args.scenario} single-lane diagnostic evidence verified for "
            f"{next(iter(lanes))}; parity not claimed"
        )
        return 0

    first_lane = sorted(lanes)[0]
    for evidence_id in evidence_ids:
        expected = normalize(records[(first_lane, evidence_id)]["semantic"])
        for lane in sorted(lanes - {first_lane}):
            actual = normalize(records[(lane, evidence_id)]["semantic"])
            if actual != expected:
                paths = ", ".join(differing_paths(expected, actual)[:8])
                raise SystemExit(
                    f"semantic evidence mismatch for {args.scenario}/{evidence_id} "
                    f"({first_lane} vs {lane}): {paths}"
                )
    print(
        f"{args.scenario} semantic evidence matches for {len(lanes)} lanes "
        f"({len(evidence_ids)} record(s))"
    )
    return 0


SOCKET_PATH = "/var/run/docker.sock"


def log(start: float, message: str) -> None:
    print(f"[{time.time() - start:7.3f}s] {message}", flush=True)


def connect() -> socket.socket:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(20)
    sock.connect(SOCKET_PATH)
    return sock


def read_head(sock: socket.socket) -> tuple[bytes, bytes]:
    buffer = b""
    while b"\r\n\r\n" not in buffer:
        chunk = sock.recv(1)
        if not chunk:
            break
        buffer += chunk
    if b"\r\n\r\n" not in buffer:
        raise RuntimeError("Docker response ended before headers")
    head, initial = buffer.split(b"\r\n\r\n", 1)
    return head, initial


def status_code(head: bytes) -> int:
    try:
        return int(head.split(b" ", 2)[1])
    except (IndexError, ValueError) as error:
        raise RuntimeError(f"invalid Docker response head: {head[:120]!r}") from error


def content_length(head: bytes) -> int:
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            return int(line.split(b":", 1)[1].strip())
    return 0


def read_body(sock: socket.socket, head: bytes, initial: bytes) -> bytes:
    expected = content_length(head)
    body = initial
    while len(body) < expected:
        body += sock.recv(4096)
    return body[:expected]


def normalize_output(raw: bytes) -> str:
    """Decode Docker raw-stream frames while preserving plain output."""
    chunks: list[bytes] = []
    offset = 0
    while len(raw) - offset >= 8 and raw[offset] in (0, 1, 2, 3):
        size = int.from_bytes(raw[offset + 4 : offset + 8], "big")
        end = offset + 8 + size
        if end > len(raw):
            break
        chunks.append(raw[offset + 8 : end])
        offset = end
    if chunks and offset == len(raw):
        raw = b"".join(chunks)
    return raw.decode("utf-8", errors="replace").replace("\r\n", "\n")


def docker_probe(variant: str, headers: str, half_close: bool, start: float) -> dict[str, Any]:
    body = json.dumps(
        {"Image": "busybox:latest", "Cmd": ["echo", f"probe={variant}"]},
        separators=(",", ":"),
    ).encode()
    create = connect()
    try:
        request = (
            f"POST /v1.51/containers/create?name=probe-{variant} HTTP/1.1\r\n"
            "Host: docker\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n{headers}\r\n"
        ).encode()
        create.sendall(request + body)
        create_head, create_initial = read_head(create)
        create_body = read_body(create, create_head, create_initial)
        create_status = status_code(create_head)
        container_id = json.loads(create_body)["Id"]
        log(start, f"{variant}: create status={create_status} id={container_id[:12]}")
    finally:
        create.close()

    attach = connect()
    start_sock = None
    wait = None
    try:
        attach_request = (
            f"POST /v1.51/containers/{container_id}/attach?stderr=1&stdout=1&stream=1 HTTP/1.1\r\n"
            f"Host: docker\r\nContent-Length: 0\r\n{headers}\r\n"
        ).encode()
        attach.sendall(attach_request)
        attach_head, attach_initial = read_head(attach)
        attach_status = status_code(attach_head)
        log(start, f"{variant}: attach status={attach_status}")
        if half_close:
            attach.shutdown(socket.SHUT_WR)
            log(start, f"{variant}: client half-closed write side")

        start_sock = connect()
        start_sock.sendall(
            (
                f"POST /v1.51/containers/{container_id}/start HTTP/1.1\r\n"
                "Host: docker\r\nContent-Length: 0\r\n\r\n"
            ).encode()
        )
        start_head, _ = read_head(start_sock)
        start_status = status_code(start_head)
        log(start, f"{variant}: start status={start_status}")

        output = attach_initial
        try:
            while True:
                chunk = attach.recv(4096)
                if not chunk:
                    break
                output += chunk
        except socket.timeout:
            log(start, f"{variant}: attach timeout ({len(output)} bytes)")

        wait = connect()
        wait.sendall(
            (
                f"POST /v1.51/containers/{container_id}/wait HTTP/1.1\r\n"
                "Host: docker\r\nContent-Length: 0\r\n\r\n"
            ).encode()
        )
        wait_head, wait_initial = read_head(wait)
        wait_status = status_code(wait_head)
        wait_body = wait_initial
        while b"}" not in wait_body:
            wait_body += wait.recv(4096)
        json_start = wait_body.find(b"{")
        json_end = wait_body.rfind(b"}") + 1
        wait_json = json.loads(wait_body[json_start:json_end])
        exit_code = wait_json.get("StatusCode")
        log(start, f"{variant}: wait status={wait_status} exit={exit_code}")
        return {
            "variant": variant,
            "create_status": create_status,
            "attach_status": attach_status,
            "start_status": start_status,
            "wait_status": wait_status,
            "exit_code": exit_code,
            "stdout": normalize_output(output),
        }
    finally:
        if wait is not None:
            wait.close()
        if start_sock is not None:
            start_sock.close()
        attach.close()


def run_docker_probe(args: argparse.Namespace) -> int:
    start = time.time()
    results = [
        docker_probe("upgrade", "Connection: Upgrade\r\nUpgrade: tcp\r\n", False, start),
        docker_probe("fin", "Connection: Upgrade\r\nUpgrade: tcp\r\n", True, start),
        docker_probe("plain", "", False, start),
    ]
    payload = {
        "schema": "velnor.fixture.docker-lease-probe.v1",
        "scenario": "docker-lease-probe",
        "evidence_id": "raw-wire",
        "lane": args.lane,
        "runner_name": args.runner_name,
        "semantic": {"variants": results},
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote Docker lease evidence to {output}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    subparsers = root.add_subparsers(dest="command", required=True)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--directory", required=True)
    compare_parser.add_argument("--scenario", required=True)
    compare_parser.add_argument("--lanes", nargs="+", required=True)
    compare_parser.set_defaults(function=compare)

    docker_parser = subparsers.add_parser("docker-probe")
    docker_parser.add_argument("--lane", required=True, choices=("github", "velnor"))
    docker_parser.add_argument("--runner-name", required=True)
    docker_parser.add_argument("--output", required=True)
    docker_parser.set_defaults(function=run_docker_probe)
    return root


if __name__ == "__main__":
    arguments = parser().parse_args()
    raise SystemExit(arguments.function(arguments))

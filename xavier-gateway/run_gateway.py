#!/usr/bin/env python3
"""GTM Telemetry Gateway entry point."""
import argparse
import os

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="GTM Telemetry Gateway")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--api-port", type=int, default=8420, help="API port")
    parser.add_argument("--log-dir", type=str, default="./sessions", help="Session log directory")
    args = parser.parse_args()

    os.environ["GTM_LOG_DIR"] = args.log_dir
    os.environ["GTM_SERIAL_PORT"] = args.port
    os.environ["GTM_SERIAL_BAUD"] = str(args.baud)

    uvicorn.run("gateway.api:app", host="0.0.0.0", port=args.api_port, log_level="info")


if __name__ == "__main__":
    main()

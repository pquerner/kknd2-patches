#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from patches import discover_patches

DEFAULT_EXE_PATH = "/home/paco/steam/common/KKnD 2 Krossfire/kknd2.exe"

def load_exe(path: Path) -> bytearray:
    if not path.exists():
        print(f"Error: Executable not found at {path}")
        sys.exit(1)
    with open(path, "rb") as f:
        return bytearray(f.read())

def save_exe(path: Path, data: bytearray):
    with open(path, "wb") as f:
        f.write(data)

def main():
    parser = argparse.ArgumentParser(description="KKND2 Executable Patch Manager")
    parser.add_argument(
        "--exe",
        type=Path,
        default=Path(DEFAULT_EXE_PATH),
        help="Path to kknd2.exe"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list / status
    subparsers.add_parser("status", help="Show status of all available patches")
    subparsers.add_parser("list", help="List all available patches")

    # enable
    p_enable = subparsers.add_parser("enable", help="Enable a patch")
    p_enable.add_argument("patch_name", help="Name of the patch to enable")

    # disable
    p_disable = subparsers.add_parser("disable", help="Disable a patch")
    p_disable.add_argument("patch_name", help="Name of the patch to disable")

    # toggle
    p_toggle = subparsers.add_parser("toggle", help="Toggle a patch on or off")
    p_toggle.add_argument("patch_name", help="Name of the patch to toggle")

    args = parser.parse_args()
    patches = discover_patches()

    if args.command in ["status", "list"]:
        data = load_exe(args.exe)
        print(f"Target executable: {args.exe}\n")
        print("Available Patches:")
        for name, patch in patches.items():
            applied = patch.is_applied(data)
            status_str = "[ENABLED]" if applied else "[DISABLED]"
            print(f"  {status_str:10s} {name:20s} - {patch.description}")
        return

    patch_name = args.patch_name
    if patch_name not in patches:
        print(f"Error: Unknown patch '{patch_name}'. Available patches: {', '.join(patches.keys())}")
        sys.exit(1)

    patch = patches[patch_name]
    data = load_exe(args.exe)
    currently_applied = patch.is_applied(data)

    if args.command == "enable":
        if currently_applied:
            print(f"Patch '{patch_name}' is already enabled.")
        else:
            patch.apply(data)
            save_exe(args.exe, data)
            print(f"Successfully enabled patch '{patch_name}'.")

    elif args.command == "disable":
        if not currently_applied:
            print(f"Patch '{patch_name}' is already disabled.")
        else:
            patch.remove(data)
            save_exe(args.exe, data)
            print(f"Successfully disabled patch '{patch_name}'.")

    elif args.command == "toggle":
        if currently_applied:
            patch.remove(data)
            save_exe(args.exe, data)
            print(f"Patch '{patch_name}' has been DISABLED.")
        else:
            patch.apply(data)
            save_exe(args.exe, data)
            print(f"Patch '{patch_name}' has been ENABLED.")

if __name__ == "__main__":
    main()

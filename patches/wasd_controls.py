import struct
from patches.base import BasePatch

class WASDControlsPatch(BasePatch):
    """
    Patch to enable WASD camera movement in KKND2: Krossfire while disabling
    all original single-key shortcut actions bound to W, A, S, and D.

    Reverse-Engineering Findings:
    - The KKND2 input engine continuously polls keys using GetAsyncKeyState() in FUN_00431970.
    - Active key state is tracked via a 32-bit bitfield where:
        - 0x00000001 = Camera Scroll UP
        - 0x00000002 = Camera Scroll DOWN
        - 0x00000004 = Camera Scroll LEFT
        - 0x00000008 = Camera Scroll RIGHT
    - Keys are mapped to bitmasks by an array of (Scancode, Bitmask) pairs originally located
      at DAT_004b3258 in the .data section.
    - Single-key actions (e.g. Stop unit, Defend order, Allies menu) are dispatched via two tables:
        1. DAT_004b77d8: Single-key action function index array.
        2. DAT_004b7860: Default UI hotkey binding structure (where offset +0x7c maps 'A' to the Allies/Bündnisse menu).

    Fix Details:
    - Custom Key Table: Relocated to the unused space of the .patch section at VA 0x0056b460 (file offset 0xeca60).
    - 'W' (Scancode 0x11): Mapped ONLY to Scroll UP (0x1). Action in DAT_004b77d8[17] cleared to -1.
    - 'A' (Scancode 0x1e): Mapped ONLY to Scroll LEFT (0x4). Default Allies menu hotkey in DAT_004b7860+0x7c cleared to -1.
    - 'S' (Scancode 0x1f): Mapped ONLY to Scroll DOWN (0x2). Removed bit 0x8000 (which previously triggered unit Stop + voice audio).
    - 'D' (Scancode 0x20): Mapped ONLY to Scroll RIGHT (0x8). Removed bit 0x10000 (unit Defend/Move order) and cleared DAT_004b77d8[32].
    """

    name = "wasd_controls"
    description = "Enables W-A-S-D keys for camera movement exclusively, disabling conflicting shortcuts."

    # Virtual address & file offset for our custom key mapping table in the .patch section.
    NEW_TABLE_VA = 0x0056b460
    NEW_TABLE_OFFSET = 0xeca60

    # Original key mapping table virtual address in .data section.
    ORIG_TABLE_VA = 0x004b3258

    # File offsets in the .text section (code) that pass the key mapping table pointer to FUN_00431900.
    REF_OFFSETS = [0x388b9, 0x38ca3, 0x39646]

    # Overrides for single-key action dispatch table (DAT_004b77d8) and default key bindings (DAT_004b7860).
    # Disables original secondary actions for W, A, S, and D:
    #   - 0x000b5e1c: DAT_004b77d8[17] ('W' key) -> Set to -1 (0xffffffff) to clear original action.
    #   - 0x000b5e58: DAT_004b77d8[32] ('D' key) -> Set to -1 (0xffffffff) to clear unit defend order.
    #   - 0x000b5edc: DAT_004b7860+0x7c ('A' key binding for Allies/Bündnisse menu) -> Set to -1 (0xffffffff) to clear Allies menu shortcut.
    ACTION_TABLE_OVERRIDES = [
        (0x000b5e1c, 0xffffffff),  # Clear 'W' action (was 0x0000001d)
        (0x000b5e58, 0xffffffff),  # Clear 'D' action (was 0x00000039 - Defend order)
        (0x000b5edc, 0xffffffff),  # Clear 'A' action (was 0x0000001e - Allies/Bündnisse menu shortcut)
    ]

    ORIG_ACTION_TABLE_VALUES = [
        (0x000b5e1c, 0x0000001d),
        (0x000b5e58, 0x00000039),
        (0x000b5edc, 0x0000001e),
    ]

    # Table of key mappings: (Scancode Index, Bitmask).
    # Camera scroll bitmasks in KKND2 engine:
    #   0x00000001 = Scroll UP
    #   0x00000002 = Scroll DOWN
    #   0x00000004 = Scroll LEFT
    #   0x00000008 = Scroll RIGHT
    ENTRIES = [
        (0x48, 0x00000001),  # Up Arrow    -> Scroll UP
        (0x50, 0x00000002),  # Down Arrow  -> Scroll DOWN
        (0x4b, 0x00000004),  # Left Arrow  -> Scroll LEFT
        (0x4d, 0x00000008),  # Right Arrow -> Scroll RIGHT
        (0x1d, 0x00000020),  # Ctrl
        (0x38, 0x00000040),  # Alt
        (0x2a, 0x00000010),  # LShift
        (0x01, 0x00000080),  # Esc
        (0x47, 0x00000100),  # Home
        (0x0f, 0x00000200),  # Tab
        (0x29, 0x00100000),  # ~
        (0x2b, 0x00000400),  # \
        (0x34, 0x00000800),  # .
        (0x33, 0x00001000),  # ,
        (0x0e, 0x00002000),  # Backspace
        (0x13, 0x00200000),  # R
        (0x21, 0x00004000),  # F
        (0x1f, 0x00000002),  # 'S' key (scancode 31) -> Scroll DOWN ONLY (removed 0x8000 Stop/Voice sound)
        (0x20, 0x00000008),  # 'D' key (scancode 32) -> Scroll RIGHT ONLY (removed 0x10000 Move/Defend order)
        (0x26, 0x00020000),  # L
        (0x16, 0x00040000),  # U
        (0x39, 0x00080000),  # Space
        (0x14, 0x08000000),  # T
        (0x0c, 0x10000000),  # -
        (0x3b, 0x02000000),  # F1
        (0x3c, 0x04000000),  # F2
        (0x3d, 0x01000000),  # F3
        (0x3e, 0x00800000),  # F4
        (0x44, 0x20000000),  # F10
        (0x57, 0x40000000),  # F11
        (0x1c, 0x00400000),  # Enter
        (0x22, 0x80000000),  # G
        (0x11, 0x00000001),  # 'W' key (scancode 17) -> Scroll UP ONLY
        (0x1e, 0x00000004),  # 'A' key (scancode 30) -> Scroll LEFT ONLY (Allies shortcut cleared above)
        (0x00, 0x00000000),  # Terminator (End of Table)
    ]

    def _get_table_bytes(self) -> bytearray:
        buf = bytearray()
        for key_idx, mask in self.ENTRIES:
            buf.extend(struct.pack('<II', key_idx, mask))
        return buf

    def is_applied(self, data: bytearray) -> bool:
        new_va_bytes = struct.pack('<I', self.NEW_TABLE_VA)
        for off in self.REF_OFFSETS:
            if data[off:off+4] != new_va_bytes:
                return False
        return True

    def apply(self, data: bytearray) -> bool:
        table_bytes = self._get_table_bytes()
        new_va_bytes = struct.pack('<I', self.NEW_TABLE_VA)

        # Write custom WASD key map table into the free space of .patch section
        data[self.NEW_TABLE_OFFSET : self.NEW_TABLE_OFFSET + len(table_bytes)] = table_bytes

        # Update key table pointers in .text section
        for off in self.REF_OFFSETS:
            data[off : off + 4] = new_va_bytes

        # Override action table & default bindings to clear conflicting shortcuts for W, A, S, D
        for off, val in self.ACTION_TABLE_OVERRIDES:
            data[off : off + 4] = struct.pack('<I', val)

        return True

    def remove(self, data: bytearray) -> bool:
        if not self.is_applied(data):
            return False

        orig_va_bytes = struct.pack('<I', self.ORIG_TABLE_VA)

        # Restore pointers back to original key table
        for off in self.REF_OFFSETS:
            data[off : off + 4] = orig_va_bytes

        # Restore original action table & default binding values
        for off, val in self.ORIG_ACTION_TABLE_VALUES:
            data[off : off + 4] = struct.pack('<I', val)

        # Zero out the custom table in .patch section
        table_len = len(self._get_table_bytes())
        data[self.NEW_TABLE_OFFSET : self.NEW_TABLE_OFFSET + table_len] = b'\x00' * table_len

        return True

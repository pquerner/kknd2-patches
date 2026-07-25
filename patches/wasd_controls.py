import struct
from patches.base import BasePatch

class WASDControlsPatch(BasePatch):
    """
    Patch to enable W-A-S-D keys for camera movement in KKND2: Krossfire while disabling
    all original single-key shortcuts and menu toggles bound to W, A, S, and D.

    ========================================================================================
    REVERSE-ENGINEERING DETAILS & ANALYSIS:
    ========================================================================================

    1. Input Polling Routine (FUN_00431970):
       - The game engine continuously polls keyboard states frame-by-frame using the Win32 API
         `GetAsyncKeyState()` within `FUN_00431970`.
       - Active movement state is maintained in a 32-bit bitfield (_DAT_004f1f40):
           - 0x00000001 = Scroll Camera UP
           - 0x00000002 = Scroll Camera DOWN
           - 0x00000004 = Scroll Camera LEFT
           - 0x00000008 = Scroll Camera RIGHT

    2. Key-to-Bitmask Mapping Array (DAT_004b3258):
       - Key scancodes are mapped to bitfield flags by an array of 8-byte (Scancode, Bitmask)
         pairs originally located at VA 0x004b3258 (.data section).
       - Originally:
           - Up Arrow (0x48) -> 0x00000001
           - Down Arrow (0x50) -> 0x00000002
           - Left Arrow (0x4b) -> 0x00000004
           - Right Arrow (0x4d) -> 0x00000008
           - 'S' Key (0x1f) -> 0x00008000 (Stop unit command + audio response)
           - 'D' Key (0x20) -> 0x00010000 (Defend / Move unit command)

    3. Custom Relocated Key Table:
       - We construct an expanded table containing WASD mappings alongside the original Arrow keys.
       - The table is placed in free space in the .patch section at VA 0x0056b460 (file offset 0xeca60).
       - Code pointers in .text passing the table to FUN_00431900 (offsets 0x388b9, 0x38ca3, 0x39646)
         are updated to point to 0x0056b460.

    4. Disabling Conflicting Hotkeys & Menu Shortcuts:
       - Single-key actions & UI menu hotkeys are registered across two tables:
           a) Single-Key Action Dispatch Table (DAT_004b77d8):
              - Index 17 ('W') -> Action 0x1d (cleared to -1 / 0xffffffff).
              - Index 32 ('D') -> Action 0x39 (Defend order, cleared to -1 / 0xffffffff).
           b) UI Hotkey Binding Structure (DAT_004b7860):
              - Offset +0x7c (0x000b5edc) -> Bound scancode 30 ('A') to Allies/Bündnisse menu (cleared to -1).
              - Offset +0xd4 (0x000b5f34) -> Bound scancode 17 ('W') to Menu toggle (cleared to -1).
              - Offset +0xc4 (0x000b5f24) -> Bound scancode 31 ('S') to UI shortcut (cleared to -1).
              - Offset +0x88 (0x000b5ee8) -> Bound scancode 32 ('D') to UI shortcut (cleared to -1).

       - In addition, the original bitmasks for 'S' (0x8000) and 'D' (0x10000) in the mapping table
         are replaced with pure scroll masks (0x2 for Down, 0x8 for Right).

    ========================================================================================
    """

    name = "wasd_controls"
    description = "Enables W-A-S-D keys for camera movement exclusively, disabling conflicting shortcuts and menu toggles."

    # Virtual address & file offset for custom key mapping table in the .patch section.
    NEW_TABLE_VA = 0x0056b460
    NEW_TABLE_OFFSET = 0xeca60

    # Original key mapping table virtual address in .data section.
    ORIG_TABLE_VA = 0x004b3258

    # File offsets in .text section that pass key table pointer to FUN_00431900.
    REF_OFFSETS = [0x388b9, 0x38ca3, 0x39646]

    # File offsets & values for overriding action dispatch table (DAT_004b77d8) and default UI bindings (DAT_004b7860).
    # Overriding with -1 (0xffffffff) completely disables secondary actions/menu toggles for W, A, S, and D keys.
    ACTION_TABLE_OVERRIDES = [
        (0x000b5e1c, 0xffffffff),  # DAT_004b77d8[17]: Clear 'W' action (was 0x0000001d)
        (0x000b5e58, 0xffffffff),  # DAT_004b77d8[32]: Clear 'D' action (was 0x00000039 - Defend order)
        (0x000b5edc, 0xffffffff),  # DAT_004b7860+0x7c: Clear 'A' menu shortcut (was scancode 30 / 'A' -> Allies/Bündnisse menu)
        (0x000b5f34, 0xffffffff),  # DAT_004b7860+0xd4: Clear 'W' menu shortcut (was scancode 17 / 'W' -> Menu toggle)
        (0x000b5f24, 0xffffffff),  # DAT_004b7860+0xc4: Clear 'S' menu shortcut (was scancode 31 / 'S')
        (0x000b5ee8, 0xffffffff),  # DAT_004b7860+0x88: Clear 'D' menu shortcut (was scancode 32 / 'D')
    ]

    ORIG_ACTION_TABLE_VALUES = [
        (0x000b5e1c, 0x0000001d),
        (0x000b5e58, 0x00000039),
        (0x000b5edc, 0x0000001e),
        (0x000b5f34, 0x00000011),
        (0x000b5f24, 0x0000001f),
        (0x000b5ee8, 0x00000020),
    ]

    # Table of key mappings: (Scancode Index, Bitmask).
    # Engine Camera Scroll Bitfield Flags:
    #   0x00000001 = Scroll UP
    #   0x00000002 = Scroll DOWN
    #   0x00000004 = Scroll LEFT
    #   0x00000008 = Scroll RIGHT
    ENTRIES = [
        (0x48, 0x00000001),  # Up Arrow    (scancode 72) -> Scroll UP
        (0x50, 0x00000002),  # Down Arrow  (scancode 80) -> Scroll DOWN
        (0x4b, 0x00000004),  # Left Arrow  (scancode 75) -> Scroll LEFT
        (0x4d, 0x00000008),  # Right Arrow (scancode 77) -> Scroll RIGHT
        (0x1d, 0x00000020),  # Ctrl        (scancode 29)
        (0x38, 0x00000040),  # Alt         (scancode 56)
        (0x2a, 0x00000010),  # LShift      (scancode 42)
        (0x01, 0x00000080),  # Esc         (scancode 1)
        (0x47, 0x00000100),  # Home        (scancode 71)
        (0x0f, 0x00000200),  # Tab         (scancode 15)
        (0x29, 0x00100000),  # ~           (scancode 41)
        (0x2b, 0x00000400),  # \           (scancode 43)
        (0x34, 0x00000800),  # .           (scancode 52)
        (0x33, 0x00001000),  # ,           (scancode 51)
        (0x0e, 0x00002000),  # Backspace   (scancode 14)
        (0x13, 0x00200000),  # R           (scancode 19)
        (0x21, 0x00004000),  # F           (scancode 33)
        (0x1f, 0x00000002),  # 'S' Key     (scancode 31) -> Scroll DOWN ONLY (removed 0x8000 Stop/Voice sound)
        (0x20, 0x00000008),  # 'D' Key     (scancode 32) -> Scroll RIGHT ONLY (removed 0x10000 Move/Defend order)
        (0x26, 0x00020000),  # L           (scancode 38)
        (0x16, 0x00040000),  # U           (scancode 22)
        (0x39, 0x00080000),  # Space       (scancode 57)
        (0x14, 0x08000000),  # T           (scancode 20)
        (0x0c, 0x10000000),  # -           (scancode 12)
        (0x3b, 0x02000000),  # F1          (scancode 59)
        (0x3c, 0x04000000),  # F2          (scancode 60)
        (0x3d, 0x01000000),  # F3          (scancode 61)
        (0x3e, 0x00800000),  # F4          (scancode 62)
        (0x44, 0x20000000),  # F10         (scancode 68)
        (0x57, 0x40000000),  # F11         (scancode 87)
        (0x1c, 0x00400000),  # Enter       (scancode 28)
        (0x22, 0x80000000),  # G           (scancode 34)
        (0x11, 0x00000001),  # 'W' Key     (scancode 17) -> Scroll UP ONLY (Menu shortcut cleared)
        (0x1e, 0x00000004),  # 'A' Key     (scancode 30) -> Scroll LEFT ONLY (Allies/Bündnisse shortcut cleared)
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

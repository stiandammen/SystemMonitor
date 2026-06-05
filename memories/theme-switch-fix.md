# Theme Switch Fix for SystemMonitor

## Problem
The application crashed with a `RuntimeError: wrapped C/C++ object of type QLabel has been deleted` when switching themes. This occurred in the `ProcessIoTable.update_processes` method when trying to hide or show the `_empty_label` widget after it had been deleted during a theme change.

## Root Cause
In `ProcessIoTable._setup_ui`, which is connected to the theme change signal, the method deleted all child widgets that were not in the `_rows` list. This included the `_empty_label` widget (a QLabel). However, the reference to `_empty_label` was not cleared, leaving a dangling pointer. When subsequent data updates called `update_processes`, the code attempted to use this deleted object, causing the crash.

## Solution
1. In `ProcessIoTable._setup_ui`, when deleting child widgets, explicitly check if the deleted widget is the `_empty_label` and set the reference to `None` if so.
2. In `ProcessIoTable.update_processes`, add null checks before calling `show()` or `hide()` on `_empty_label`.

## Changes Made
- Modified `src/systemmonitor/widgets/storage_widgets.py` in the `ProcessIoTable` class:
  - Updated `_setup_ui` to clear `self._empty_label` when deleting the widget.
  - Updated `update_processes` to check `if self._empty_label:` before calling `show()` or `hide()`.

## Verification
After applying these changes, theme switching should no longer cause the application to crash. The process table will correctly show/hide the "No significant activity detected" label based on whether there are processes to display.

## Notes
- This fix addresses the immediate crash. A separate issue exists where header and empty label widgets are not updated on theme change (their style sheets are not refreshed), but this does not cause crashes and can be addressed in a future update.
- The changes are minimal and safe, only adding null checks and reference clearing.
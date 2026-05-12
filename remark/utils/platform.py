"""
平台检查工具
"""

import platform

from remark.i18n import _ as _


def check_platform() -> bool:
    if platform.system() != "Windows":
        try:
            from tkinter import messagebox

            messagebox.showerror(
                _("Error"),
                _("This tool adds remarks to folders on Windows. Other systems are not supported.\nCurrent system: {system}").format(
                    system=platform.system()
                ),
            )
        except Exception:
            pass
        return False
    return True

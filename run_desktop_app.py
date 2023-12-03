import traceback
import tkinter.messagebox
import desktop_app.src.view as view
import desktop_app.src.controller as controller
from desktop_app.src.view_model import ViewModel

from model import persistence


if __name__ == "__main__":
    CONFIG_FILE_NAME_DESKTOP_APP = "desktop_app/resources/config.sample.json"
    try:
        model = ViewModel(
            persistence.Persistence(config_file_path=CONFIG_FILE_NAME_DESKTOP_APP)
        )
        view = view.View()
        controller = controller.Controller(view, model)
        controller.mainloop()
    except Exception as exc:
        message = traceback.format_exception_only(type(exc), exc)[0]
        if len(message) == 0:
            message = traceback.format_exc()
        tkinter.messagebox.showerror(title="Application start error", message=message)

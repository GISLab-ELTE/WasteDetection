import view
from model import model, persistence
import traceback
import controller
import tkinter.messagebox


if __name__ == "__main__":
    try:
        model = model.Model(persistence.Persistence())
        view = view.View()
        controller = controller.Controller(view, model)
        controller.mainloop()
    except Exception as exc:
        message = traceback.format_exception_only(type(exc), exc)[0]
        if len(message) == 0:
            message = traceback.format_exc()
        tkinter.messagebox.showerror(
            title="Application start error",
            message=message
        )

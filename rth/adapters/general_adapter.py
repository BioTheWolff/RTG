from rth.core.dispatcher import Dispatcher
from rth.core.errors import WrongOptionName


class GeneralAdapter:
    file_path = None

    def __init__(self, file_path, ignore=False, debug=False):
        self.file_path = file_path
        self.ignore = ignore
        self.debug = debug

    def __call__(self, *args, **kwargs):
        return self.evaluate()

    def evaluate(self):
        pass

    def _process(self, subnetworks, routers, links, options=None):
        dispatch = Dispatcher(debug=self.debug)

        if options:
            for name in options:
                if self.ignore:
                    try:
                        dispatch.set_option(name, options[name])
                    except WrongOptionName:
                        # Only catch when option name is invalid, not when the value type doesn't match the expected one
                        pass
                else:
                    dispatch.set_option(name, options[name])

        dispatch.execute(subnetworks, routers, links)

        return dispatch

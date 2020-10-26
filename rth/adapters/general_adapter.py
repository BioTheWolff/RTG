from rth.core.dispatcher import Dispatcher


class GeneralAdapter:
    file_path = None

    def __init__(self, file_path):
        self.file_path = file_path

    def __call__(self, *args, **kwargs):
        return self.evaluate()

    def evaluate(self):
        pass

    @staticmethod
    def _process(subnetworks, routers, links, options=None):
        dispatch = Dispatcher()
        dispatch.execute(subnetworks, routers, links)

        return dispatch

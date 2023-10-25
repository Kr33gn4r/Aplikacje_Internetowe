import threading
class ThreadJob(threading.Thread):
    def __init__(self, callback, event, frequency):
        self.callback = callback
        self.event = event
        self.frequency = frequency
        super(ThreadJob, self).__init__()

    def run(self):
        while not self.event.wait(self.frequency):
            if self.event.is_set(): break
            self.callback()
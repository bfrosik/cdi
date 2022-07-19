from consumer.realtime.feed import Feed
import consumer.realtime.adapter as adapter
from epics import caget

class FeedDecorator(Feed):
    def __init__(self, decor):
        Feed.__init__(self)
        self.decor = decor


    def get_packed_data(self, data, data_type):
        decor = {}
        if 'theta' in self.decor:
            th = caget(self.decor['theta'])
            decor['theta'] = th
        if 'something' in self.decor:
            sm = caget(self.decor['something'])
            decor['something'] = sm

        return adapter.pack_data(data, data_type, decor)



import _thread


class MicroPyQueue(object):
    """ Special Queue for sending commands and getting return items from a MicroPython Process

    """

    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.items = []

    def put(self, item):
        """ Put an item into the queue

        :param item: dict of format, {"method": <class_method>, "args": <args>}
        :return: None
        """
        with self.lock:
            self.items.append(item)

    def get(self, method=None, all=False):
        """ Get an item from the queue

        :param method: set to class_method to return a specific result
        :param all: when set return all
        :return: return item(s) in list
        """
        with self.lock:
            if method is None:
                if all:
                    ret = self.items
                    self.items = []
                    return ret

                if self.items: return [self.items.pop(0)]
                else: return []

            items = []
            for idx, item in enumerate(self.items):
                if item["method"] == method:
                    items.append(self.items.pop(idx))
                    if not all:
                        break

            return items

    def peek(self, method=None, all=False):
        """ Peek at item(s) in the queue, does not remove item(s)

        :param method: if set, returns first item matching method string
        :param all: if set returns all items, if method is set, then all items with method returned
        :return: None for no item, or [item(s)]
        """
        with self.lock:
            if method is None:
                if all:
                    return self.items

                if self.items: return [self.items[0]]
                else: return []

            items = []
            for idx, item in enumerate(self.items):
                if item["method"] == method:
                    items.append(self.items[idx])
                    if not all:
                        break

            return items

    def update(self, item_update):
        """ Update an item in queue, or append item if it doesn't exist

        :param item_update: new item, of format, {"method": <class_method>, "args": <args>}
        :return:
        """
        with self.lock:
            if self.items:
                for idx, item in enumerate(self.items):
                    if item["method"] == item_update["method"]:
                        self.items[idx] = item_update
                        return

            # if no matching, append this item
            self.items.append(item)

#! /usr/bin/env python
# -*- coding: utf-8 -*-

class MicroPyQueue(object):
    """ Special Queue for sending commands and getting return items from a MicroPython Process

    """
    MAX_ITEMS = 10

    def __init__(self, max_items=MAX_ITEMS):
        self.items = []
        self.max_items = max_items

    def put(self, item):
        """ Put an item into the queue

        :param item: dict of format, {"method": <class_method>, "args": <args>}
        :return: True on queue, False on error or too many items
        """
        ret = True
        if len(self.items) >= self.max_items:
            self.items.pop()
            ret = False
        self.items.append(item)
        return ret

    def get(self, method=None, all=False):
        """ Get an item from the queue

        :param method: set to class_method to return a specific result
        :param all: when set return all
        :return: [item, ...]
        """
        if method is None:
            if all:
                ret = self.items
                self.items = []
                return ret

            if self.items: return [self.items.pop(0)]
            else: return []

        items = []
        for idx, item in enumerate(self.items):
            if item["method"] == method or item["method"] == "_debug":
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
        if self.items:
            for idx, item in enumerate(self.items):
                if item["method"] == item_update["method"]:
                    self.items[idx] = item_update
                    return

        # if no matching, append this item
        self.items.append(item)

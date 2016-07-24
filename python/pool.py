class MessageIdPool:
    def __init__(self):
        self.next_id = 1
        self.pool = set()

    def get_id(self):
        if len(self.pool) > 0:
            return self.pool.pop()
        else:
            to_return = self.next_id
            self.next_id += 1
            return to_return

    def return_id(self, n):
        if n in self.pool:
            raise ValueError("Pool already has id {}".format(n))
        self.pool.add(n)

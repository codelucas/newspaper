
class Test(object):

    def __init__(self):
        self.ll = range(11)

    def _purge_list(self, ll=None):
        cur_ll = self.ll if not ll else ll

        for index, e in enumerate(cur_ll):
            if e % 2 == 0:
                del cur_ll[index]
        return cur_ll

    def purge_list(self):
        self.ll = self._purge_list()


if __name__ == '__main__':
    t = Test()

    print t.ll
    print 'purging list'

    t.purge_list()

    print t.ll

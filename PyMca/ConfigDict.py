#/*##########################################################################
# Copyright (C) 2004-2012 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# This toolkit is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# PyMca is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# PyMca; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# PyMca follows the dual licensing model of Riverbank's PyQt and cannot be
# used as a free plugin for a non-free program.
#
# Please contact the ESRF industrial unit (industry@esrf.fr) if this license
# is a problem for you.
#############################################################################*/
import sys
import string
if sys.version < '3.0':
    import ConfigParser
else:
    import configparser as ConfigParser
try:
    import numpy.oldnumeric as Numeric
except:
    pass

class ConfigDict(dict):

    def __init__(self, defaultdict={}, initdict=None, filelist=None):
        dict.__init__(self, defaultdict)
        self.default= defaultdict
        self.filelist= []

        if initdict is not None:
            self.update(initdict)
        if filelist is not None:
            self.read(filelist)

    def reset(self):
        """ Revert to default values
        """
        self.clear()
        self.update(self.default)

    def clear(self):
        """ Clear dictionnary
        """
        dict.clear(self)
        self.filelist= []

    def _check(self):
        pass

    def __tolist(self, mylist):
        if mylist is None: return None
        if type(mylist)!=type([]):
            return [ mylist ]
        else:
            return mylist

    def getfiles(self):
        return self.filelist

    def getlastfile(self):
        return self.filelist[len(self.filelist)-1]

    def __convert(obj, option):
        return option

    def read(self, filelist, sections=None):
        """
        read the input filename into the internal dictionary
        """
        filelist= self.__tolist(filelist)
        sections= self.__tolist(sections)

        cfg= ConfigParser.ConfigParser()
        cfg.optionxform= self.__convert
        cfg.read(filelist)
        self.__read(cfg, sections)

        for file in filelist:
                self.filelist.append([file, sections])
        self._check()

    def __read(self, cfg, sections=None):
        cfgsect= cfg.sections()

        if sections is None:
            readsect= cfgsect
        else:
            readsect= [ sect for sect in cfgsect if sect in sections ]

        for sect in readsect:
            ddict= self
            for subsectw in sect.split('.'):
                subsect = subsectw.replace("_|_",".")
                if not (subsect in ddict):
                    ddict[subsect]= {}
                ddict= ddict[subsect]
            for opt in cfg.options(sect):
                ddict[opt]= self.__parse_data(cfg.get(sect, opt))

    def __parse_data(self, data):
        if len(data):
            if data.find(',')== -1:
                #it is not a list
                if (data[0] == '[') and (data[-1] == ']'):
                    #this looks as an array
                    try:
                        return Numeric.array([float(x) for x in data[1:-1].split()])
                    except:
                        try:
                            if (data[2] == '[') and (data[-3] == ']'):
                                nrows = len(data[3:-3].split('] ['))
                                indata = data[3:-3].replace('] [',' ')
                                indata = Numeric.array([float(x) for x in \
                                                           indata.split()])
                                indata.shape = nrows,-1
                                return indata
                        except:
                            pass
        dataline= [ line for line in data.splitlines() ]
        if len(dataline)==1:
            return self.__parse_line(dataline[0])
        else:
            return [ self.__parse_line(line) for line in dataline ]
        
    def __parse_line(self, line):
        if line.find(',')!=-1:
            return [ self.__parse_string(sstr.strip()) for sstr in line.split(',') ]
        else:
            return self.__parse_string(line.strip())

    def __parse_string(self, sstr):
        try:
            return int(sstr)
        except:
            try:
                return float(sstr)
            except:
                return sstr

    def tostring(self, sections=None):
        import StringIO
        tmp= StringIO.StringIO()
        sections= self.__tolist(sections)
        self.__write(tmp, self, sections)
        return tmp.getvalue()

    def write(self, filename, sections=None):
        """
        Write the current dictionary to the given filename
        """
        sections= self.__tolist(sections)
        fp= open(filename, "w")
        self.__write(fp, self, sections)
        fp.close()

    def __write(self, fp, ddict, sections=None, secthead=None):
        retstring= ''
        dictkey= []
        listkey= []
        valkey= []
        for key in ddict.keys():
            if type(ddict[key]) == type([]):
                listkey.append(key)
            elif type(ddict[key]) == type({}):
                dictkey.append(key)
            else:
                valkey.append(key)

        for key in valkey:
            if type(ddict[key])== Numeric.ArrayType:
                fp.write('%s =' % key + ' [ '+ ' '.join([str(val) for val in ddict[key]])+' ]\n')
            else:
                fp.write('%s = %s\n'%(key, ddict[key]))

        for key in listkey:
            fp.write('%s = '%key)
            llist= []
            sep= ', '
            for item in ddict[key]:
                if type(item)==type([]):
                    llist.append(', '.join([str(val) for val in item]))
                    sep= '\n\t'
                else:
                    llist.append(str(item))
            fp.write('%s\n'%(sep.join(llist)))
        #if sections is not None:
        #    print "dictkey before = ",dictkey
        #    dictkey= [ key for key in dictkey if key in sections ]
        #    print "dictkey after = ",dictkey
        for key in dictkey:
            if secthead is None:
                newsecthead= key.replace(".","_|_")
            else:
                newsecthead = '%s.%s'%(secthead, key.replace(".","_|_"))
            #print "newsecthead = ",newsecthead
            fp.write('\n[%s]\n'%newsecthead)
            self.__write(fp, ddict[key], key,newsecthead)


def prtdict(ddict, lvl=0):
        for key in ddict.keys():
            if type(ddict[key])==type({}):
                for i in range(lvl):
                    print('\t'),
                print('+',key)
                prtdict(ddict[key], lvl+1)
            else:
                for i in range(lvl):
                    print('\t'),
                print('-', key, '=', ddict[key])

def test():
    import sys
    if len(sys.argv)>1:
        config= ConfigDict(filelist=sys.argv[1:])
        prtdict(config)
    else:
        print("USAGE: %s <filelist>"%sys.argv[0])


if __name__=='__main__':
    test()        

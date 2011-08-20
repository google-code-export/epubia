# -*- encoding: utf-8 -*-
# Plain Text to Formatted Text
#
# Added markup
#    &          null paragraph
# Disabled markup
#    -          list item
# Changed markup
#    * * *      horizontal line -> predefined paragraph separator

import codecs
import re
EMPTYLINE_PTN = re.compile(r'^\s*$',re.M|re.U)
PARAEND_PTN = re.compile(r'''([\.\?!'"\)])\s*$''',re.M|re.U)
INDENTSTART_PTN = re.compile(r'''^([ ]{1,3})''',re.M|re.U)      # preserve Markdown block (4 spaces or tab)

# guessing chapter/section
CHAP_PTN1 = re.compile(r'\n\n([^\n]+)\n[ ]*={5,}[ \t]*\n')
CHAP_PTN2 = re.compile(r'\n#[ \t]*')
CHAP_PTN3 = re.compile(ur'^\s*(제\s*\d+\s*장[ \.].{2,})$',re.M)
SECT_PTN1 = re.compile(r'\n##[ \t]*')
SECT_PTN2 = re.compile(r'^\s*([\dIVXivx]+\.?)\s*$',re.M)

class txt_cleaner:
    def __init__(self):
        self.ptn_sl_empty = re.compile(r'([^\n])\n\n([^\n])')
        self.ptn_quote_start = re.compile(r'''([\.!\?"'])\s*\n+(["'])''')
        self.ptn_quote_end = re.compile(r'''(["'])\s*\n+(\S)''')
        self.ptn_dblqt_begin = re.compile('^ *"([^"]*.) *$',re.M|re.U)
        self.ptn_dblqt_end = re.compile('^ *(.[^"]*)" *$',re.M|re.U)
        self.ptn_sglqt_begin = re.compile("^ *'([^']*.) *$",re.M|re.U)
        self.ptn_sglqt_end = re.compile("^ *(.[^']*)' *$",re.M|re.U)
        self.ptn_starhr = re.compile('(\* *\* *\*)',re.M|re.U)
        self.ptn_minusli = re.compile('^( *)-([^-])',re.M|re.U)
        self.cleaned = False

    def convert(self, txt, start=1):
        # preprocess
        txt = self.preprocess(txt, start)
        # paragraph
        txt = self.format_paragraph(txt)
        # break within word
        txt = self.recover_word(txt)
        # postprocess
        txt = self.postprocess(txt)
        return txt

    def preprocess(self, txt, start=1):
        # line skip
        if start != 1:
            print "start from %d" % start
            txt = '\n'.join( txt.split('\n')[start-1:] )
        # remove spaces in line end
        # --> space in tail can be used as line break directive
        #txt = re.compile(r'[ \r]*$',re.M).sub('', txt)
        # clean empty line
        txt = re.compile(r'^\s*$',re.M|re.U).sub('', txt)
        # filter special character
        txt = txt.replace(u'”','"').replace(u'“','"')
        txt = txt.replace(u"‘","'").replace(u"’","'")
        #txt = txt.replace(u'『',"'").replace(u'』',"'")
        return txt

    def analyze_paragraph(self, txt):
        # extract patterns
        self.num_line = len( txt.split('\n') )
        self.num_emptyline = len( EMPTYLINE_PTN.findall(txt) )
        self.num_paraend = len( PARAEND_PTN.findall(txt) )
        self.num_indentline = len( INDENTSTART_PTN.findall(txt) )
        print "paragraph: %d %d %d %d" % (self.num_line, self.num_emptyline, self.num_paraend, self.num_indentline)

    def format_paragraph(self, text):
        self.cleaned = False
        # merge multiple empty lines
        txt = re.sub(r'\n{2,}', r'\n\n', text)
        # decide paragraph style
        self.analyze_paragraph(txt)
        if self.num_emptyline > 0.45*self.num_line and self.num_paraend < 0.8*self.num_emptyline:
            # Type-5: line separated with empty line
            print "detect all lines are separated by empty line"
            txt = self.ptn_sl_empty.sub(r'\g<1>\n\g<2>',txt)
            self.cleaned = True
            self.analyze_paragraph(txt)
        if self.num_indentline > self.num_emptyline:
            # Type-2: paragraph by indent
            print "detect paragraph by indent"
            text = INDENTSTART_PTN.sub(r'\n',txt)
            self.cleaned = True
        elif self.num_emptyline < 0.3 * self.num_paraend:
            if self.num_paraend > 0.8 * self.num_line:
                # Type-3: paragraph in one line
                print "detect single line paragraph"
            else:
                # Type-4: not formatted
                print "detect non formatted paragraph"
            text = PARAEND_PTN.sub(r'\1\n',txt)
            self.cleaned = True
        return text

    def recover_word(self, text):
        numline = len(text.split('\n'))
        numsch = len(re.compile('\S\n\S ',re.U).findall(text))  # single character in line start
        #print "word break: %d / %d" % (numsch, numline)
        if numsch > numline*0.08:
            print "Suspect word break over lines"
            text = re.compile('(\w)\n([다자까아][\.\?!])',re.U).sub(r'\1\2\n',text)
            text = re.compile('(\w)\n([이가을를은는도]) ',re.U).sub(r'\1\2\n',text)
            #text = re.compile(' (\w)\n(\w{2,})',re.U).sub(r'\n\1\2',text)
        return text

    def postprocess(self, txt):
        if self.cleaned:
            # wrap single quote block with empty lines
            txt = self.ptn_quote_start.sub(r'\1\n\n\2', txt)
            txt = self.ptn_quote_end.sub(r'\1\n\n\2', txt)
        else:
            # separate adjacent quoted statements (conservative way)
            txt = re.sub(r'"\n( *)"',r'"\n\n\1"',txt)
            txt = re.sub(r"'\n( *)'",r"'\n\n\1'",txt)
        # transpose " and ' to better shapes
        txt = self.ptn_dblqt_begin.sub(ur'“\1', txt)
        txt = self.ptn_dblqt_end.sub(ur'\1”', txt)
        txt = self.ptn_sglqt_begin.sub(ur'‘\1', txt)
        txt = self.ptn_sglqt_end.sub(ur'\1’', txt)
        # Disable some markdown markers for better output
        #    1) horizontal line drawing by '* * *'
        #    2) list starting with '-' 
        #         use alternative way starting with '*' 
        txt = self.ptn_starhr.sub(r'\t\g<1>', txt)
        txt = self.ptn_minusli.sub(r'\g<1>\\-\g<2>', txt)
        return txt

def mark_chapter(text, toc_hdr):
    start = False
    inTOC = False
    cnt = 0
    for line in text.split('\n'):
    	if start:
            cname = re.compile('\d*\s*$').sub('',line).strip()
            if cname:
                inTOC = True
                #print (u"chapter: %s" % cname).encode('utf-8')
                text = re.compile('^%s$' % cname,re.M).sub('%s\n%s' % (cname,'='*2*len(cname)),text)
                cnt += 1
            elif inTOC:
                break
    	elif line.find(toc_hdr) >= 0:
            start = True
            inTOC = False
    print "%d chapters found" % cnt
    return text

def guess_block(txt):
    # chapter
    #txt = mark_chapter(txt, u'<차 례>')
    # chapter
    numch = 0
    numch += len(CHAP_PTN1.findall(txt))
    numch += len(CHAP_PTN2.findall(txt))
    if numch < 1:
        txt = CHAP_PTN3.sub(r'\n# \1\n\n', txt)
        # section
        numsec = 0
        numsec += len(SECT_PTN1.findall(txt))
        if numsec < 1:
            txt = SECT_PTN2.sub(r'\n## \1\n\n', txt)
    return txt

def guess_coding(txt, filename=''):
    if filename.find('.utf8') > 0:
        return 'utf-8'
    if filename.find('.cp949') > 0:
        return 'cp949'
    if filename.find('.euckr') > 0:
        return 'euc-kr'
    if filename.find('.johab') > 0:
        return 'johab'
    if txt[:3] == codecs.BOM_UTF8:
        return 'utf-8'
    import chardet
    detsz = min(10000, len(txt))
    coding = chardet.detect(txt[:detsz])['encoding']
    print "coding %s is detected" % coding
    if coding is None or coding == 'EUC-KR':
        coding = 'cp949'
    return coding

#--------------------------------------
def load(fname):
    # load file
    try:
        text = open(fname,'r').read()
    except:
        import sys
        print >> sys.stderr, "fail to open"
        return None
    # convert to unicode
    coding = guess_coding(text, filename=fname)
    text = unicode(text, coding, errors='replace')
    if ord(text[0]) == 0xfeff:  # utf-8 BOM
        return text[1:]
    return text

def clean(text, start=1):
    # convert
    text = txt_cleaner().convert( text, start )
    return guess_block( text )

#--------------------------------------
def extract_meta(text):
    lines = text.split('\n')
    info = {}
    meta_found = False
    for line in lines:
        if len(line.strip()) == 0:
            break   # empty line ends meta block
        pos = line.find(':')
        if pos >= 0:
            key = line[:pos].lower()
            if key[0] == ' ' or key[-1] == ' ':
                break
            val = line[pos+1:].strip() 
            info[key] = val
            meta_found = True
        elif meta_found and line.startswith(' '*4):
            info[key] += ', ' + line.strip()
        else:
            break
    return info

def insert_meta(text, meta):
    # remove existing meta block
    lines = text.split('\n')
    cnt = 0
    meta_found = False
    for line in lines:
        if len(line.strip()) == 0:
            break   # empty line ends meta block
        pos = line.find(':')
        if pos >= 0:
            meta_found = True
        elif meta_found and line.startswith(' '*4):
            pass    # continued block
        else:
            break
        cnt += 1
    # insert new meta block
    nwlns = []
    for key, val in meta.items():
        if key == 'isbn':
            key = key.upper()
        elif key.find('_') < 0:     # not cover_url
            key = key.title()
        nwlns.append( u"{0:15} {1}".format(key+':', val.replace('\n','')) )
    nwlns.append('')
    nwlns.extend( lines[cnt:] )
    return '\n'.join(nwlns)

#--------------------------------------
if __name__ == '__main__':
    import sys
    rslt = load(sys.argv[1])
    open(sys.argv[2],'w').write( rslt.encode('utf-8') )
# vim:sw=4:ts=8:et

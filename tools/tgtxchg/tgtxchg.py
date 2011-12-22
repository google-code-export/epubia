#!/usr/bin/env python
#  CSS exchanger for ePub generated by epubia
__program__ = 'tgtxchg'
__version__ = '0.1.1'

import os
import zipfile
import tempfile

#------------------------------------------------
# GUI
#------------------------------------------------
import wx

label_widget = None
idle_label = "Drop ePub file below"

class FileDropTarget(wx.FileDropTarget):
    def __init__(self, obj):
        wx.FileDropTarget.__init__(self)
        self.obj = obj

    def OnDropFiles(self, x, y, filenames):
        self.obj.log.SetInsertionPointEnd()
        gencss = os.path.join('template', 'generic.css')
        tgtcss = os.path.join('target', self.obj.css_cb.GetStringSelection()+'.css')
        fontfile = os.path.join('fonts', self.obj.font_cb.GetStringSelection())
        #print self.obj.overwrite_cb.GetValue()

        global label_widget, idle_label
        maxcnt = len(filenames)
        cnt = 0
        for filename in filenames:
            cnt += 1
            info_str = "%d / %d is processed: %s" % (cnt, maxcnt, os.path.basename(filename))
            label_widget.SetLabel(info_str)
            tgtxchg(filename, (gencss,tgtcss), fontfile)
            self.obj.log.AppendText( u"{0:s} changed\n".format(filename) )
        label_widget.SetLabel(idle_label)

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)
        panel = wx.Panel(self, wx.ID_ANY)

        #--- Top button bar
        btnszer1 = wx.BoxSizer( wx.HORIZONTAL )
        import glob

        # Target select
        tgtlabel = wx.StaticText(panel, wx.ID_ANY, "Target")
        targetList = []
        for css in glob.glob("target/*.css"):
            targetList.append( os.path.splitext(os.path.basename(css))[0] )
        self.css_cb = wx.Choice(panel, choices=targetList)
        self.css_cb.SetStringSelection(targetList[0])
        btnszer1.Add( tgtlabel, 0, wx.LEFT|wx.CENTRE|wx.RIGHT, 2 )
        btnszer1.Add( self.css_cb, 1, wx.LEFT|wx.RIGHT, 2 )

        # Font select
        tgtlabel = wx.StaticText(panel, wx.ID_ANY, "Font")
        targetList = []
        for font in glob.glob("fonts/*.[ot]tf"):
            targetList.append( os.path.basename(font) )

        self.font_cb = wx.Choice(panel, choices=targetList)
        self.font_cb.SetStringSelection(targetList[0])
        btnszer1.Add( tgtlabel, 0, wx.LEFT|wx.CENTRE|wx.RIGHT, 2 )
        btnszer1.Add( self.font_cb, 1, wx.LEFT|wx.RIGHT, 2 )

        #self.overwrite_cb = wx.CheckBox(panel, wx.ID_ANY)
        #lbl1 = wx.StaticText(panel, label="Overwrite")
        #btnszer1.Add( self.overwrite_cb, 0, wx.LEFT|wx.CENTRE|wx.RIGHT, 2 )
        #btnszer1.Add( lbl1, 0, wx.LEFT|wx.CENTRE|wx.RIGHT, 2 )

        #--- Drop zone
        global label_widget, idle_label
        tlb1 = wx.StaticText(panel, label=idle_label)
        label_widget = tlb1
        self.log = wx.TextCtrl(panel, size=(400,200),
                        style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        # set Drop zone
        self.log.SetDropTarget( FileDropTarget(self) )

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btnszer1, 0, wx.GROW|wx.LEFT|wx.RIGHT, 5)
        sizer.Add(tlb1, 0, wx.GROW|wx.LEFT|wx.RIGHT, 5)
        sizer.Add(self.log, 1, wx.GROW|wx.ALL, 5)

        panel.SetSizer(sizer)
        sizer.Fit(self)
        self.Show(True)

def gui():
    app = wx.App(False)
    frame = MyFrame(None, __program__)
    app.MainLoop()

#--------------------------------------------------
# ePub handling
#--------------------------------------------------
def tgtxchg(epubfile, tgtfiles, fontfile):
    # extract
    epub = zipfile.ZipFile(epubfile,'r')
    dir = tempfile.mkdtemp()
    epub.extractall(dir)
    epub.close()
    # replace
    import shutil
    os.remove( os.path.join(dir,'OPS','generic.css') )
    os.remove( os.path.join(dir,'OPS','target.css') )
    if os.path.exists( os.path.join(dir,'OPS','embedded.ttf') ):
        os.remove( os.path.join(dir,'OPS','embedded.ttf') )
    if os.path.exists( os.path.join(dir,'OPS','embedded.otf') ):
        os.remove( os.path.join(dir,'OPS','embedded.otf') )
    shutil.copy( tgtfiles[0], os.path.join(dir,'OPS','generic.css') )
    shutil.copy( tgtfiles[1], os.path.join(dir,'OPS','target.css') )
    if os.path.basename(tgtfiles[1]).startswith('Embed'):
        extname = os.path.splitext(fontfile)[1]
        shutil.copy( fontfile, os.path.join(dir,'OPS','embedded'+extname) )
    # archive
    tzip = tempfile.NamedTemporaryFile(prefix='epub_',suffix='.zip',delete=False)
    epub = zipfile.ZipFile(tzip,'w')
    os.path.walk(dir, epub_archive, (dir,epub))
    epub.close()
    tzip.close()
    # clean up
    shutil.rmtree(dir)
    #shutil.move(tzip.name,epubfile)
    # secure way when considering slow network drive
    shutil.move(tzip.name,epubfile+".zip")
    os.rename(epubfile,epubfile+".bak")
    os.rename(epubfile+".zip",epubfile)
    os.remove(epubfile+".bak")

def epub_archive(arg, dir, files):
    root,epub = arg
    rdir = os.path.relpath(dir,root)
    if dir is root and 'mimetype' in files:
        epub.write(os.path.join(dir,'mimetype'), 'mimetype')
        files.remove('mimetype')
    for file in files:
        #print rdir+' -> '+file
        if file.endswith('.xhtml') or file.endswith('.css'):
            epub.write(os.path.join(dir,file), os.path.join(rdir,file), zipfile.ZIP_DEFLATED)
        else:
            epub.write(os.path.join(dir,file), os.path.join(rdir,file))

if __name__ == "__main__":
    import sys
    exec_path = os.path.abspath(sys.argv[0])
    base_dir = os.path.dirname(exec_path)

    sys.path.append(base_dir)
    base_dir = os.curdir

    # option parsing
    from optparse import OptionParser

    parser = OptionParser(usage = '%prog [options] [script...]')
    parser.add_option("-c", "--common", dest="common", default="generic",
                      help="Common CSS", metavar="FILE")
    parser.add_option("-t", "--target", dest="target", default="Nothing",
                      help="Target device CSS", metavar="FILE")
    parser.add_option("-f", "--font", dest="font", default="SeoulHangang.ttf",
                      help="Font", metavar="FILE")
    options, args = parser.parse_args()

    if len(args) == 0:
        gui()
    else:
        gencss = os.path.join(base_dir, 'template', options.common+'.css')
        tgtcss = os.path.join(base_dir, 'target', options.target+'.css')
        fontfile = os.path.join(base_dir, 'fonts', options.font)
        for filename in args:
            tgtxchg(filename, (gencss,tgtcss), fontfile)

# vim:ts=4:sw=4:et

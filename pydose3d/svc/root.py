from ROOT import TFile, TIter, TH2Poly, TCanvas, gStyle, gROOT, gStyle, gPad

class RootPlotSvc():
    def __init__(self):
        pass
    
    @classmethod
    def __TCanvas(cls, name="TCanvas", w=600, h=600, logscale=True):
        can = TCanvas(name,name,w,h)
        can.SetWindowSize(w + (w - can.GetWw()), h + (h - can.GetWh()));
        if logscale:
            can.cd(0).SetLogz()
        gStyle.SetOptStat(0)
        gROOT.SetStyle()
        return can

    @classmethod
    def TCanvas(cls,obj,opts,logscale=False,title_z="None",width=900):
        # 900 - docelowa szerokość w pixelach
        can = cls.__TCanvas(logscale=logscale)
        pad = can.cd()
        gStyle.SetTitleFillColor(-1)
        gStyle.SetTitleBorderSize(0)
        gStyle.SetTitleStyle(0)
        gStyle.SetTitleW(0.9)
        obj.Draw(opts)
        can.SetRealAspectRatio()
        w = can.GetWw()
        h = can.GetWh()
        const = width/w  
        can.SetCanvasSize(int(const*w),int(const*h*0.88))
        can.SetWindowSize(int(const*w*1.1),int(const*h))
        pad.SetLeftMargin(0.12) # Def one 0.1
        pad.SetTopMargin(0.05) # Def one 0.1
        if opts=="COLZ":
            pad.SetRightMargin(0.21)
            palette = obj.GetListOfFunctions().FindObject("palette")
            palette.SetX1NDC(0.82)
            palette.SetX2NDC(0.90)
            palette.SetTitle(title_z)
            palette.SetTitleOffset(1.1) # ( Przesuwa się tylko w jednej osi... )
        gPad.Modified()
        gPad.Update()
        gStyle.SetOptStat(0)
        gROOT.SetStyle()
        return can
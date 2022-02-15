import tkinter
from tkinter import *
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import messagebox as mb
from tkinter import filedialog as fd
from Optimization import Optimization
from Classifiers.allClassifiers import (
    AdaBoosting, KNN, GaussianNB_, GradientBoosting,
    LinearSVC_, RandomForest, DecisionTree, LogisticRegression_
)
print("test branch create")

class Test():
    # @staticmethod
    def commonCombo(self, values, font, x, y, default=0):
        this = ttk.Combobox(values=values, font=font)
        this.current(default)
        this.place(y=y, x=x)
        self.allCombo[values[0]] = this

    def labelAndEntry(self, text, font, y, x, justify):
        Label(text=text, font=font, justify=justify).place(y=y, x=x)
        entry = Entry(self.top, bd=5, background='#ffffff')
        entry.place(y=y, x=x + 150)
        self.allEntry[text] = entry

    def __init__(self, fileName="data.csv"):
        self.fileName = fileName
        self.allCombo = {}
        self.allEntry = {}
        self.top = tkinter.Tk()
        fontStyle = tkFont.Font(family="Lucida Grande", size=13)
        fontStyle2 = tkFont.Font(family="Lucida Grande", size=10)
        self.commonCombo(
            values=["MSSubClass", "20", "30", "40", "45", "50", "60", "70", "75", "80", "85", "90", "120", "150", "160",
                    "180", "190"], font=fontStyle2, y=50, x=100, default=1)
        self.commonCombo(values=["MSZoning", "A", "C", "FV", "I", "RH", "RL", "RP", "RM"], font=fontStyle2, y=75, x=100,
                         default=2)
        self.commonCombo(values=["Street", "Grvl", "Pave"], font=fontStyle2, y=100, x=100, default=1)
        self.commonCombo(values=["LotShape", "Reg", "IR1", "IR2", "IR3"], font=fontStyle2, y=125, x=100, default=2)
        self.commonCombo(values=["LandContour", "Lvl", "Bnk", "HLS", "Low"], font=fontStyle2, y=150, x=100, default=3)
        self.commonCombo(values=["LotConfig", "Inside", "Corner", "CulDSac", "FR2", "FR3"], font=fontStyle2, y=175,
                         x=100, default=4)
        self.commonCombo(values=["LandSlope", "Gtl", "Mod", "Sev"], font=fontStyle2, y=200, x=100, default=1)
        self.commonCombo(
            values=["Condition1", "Artery", "Feedr", "Norm", "RRNn", "RRAn", "PosN", "PosA", "RRNe", "RRAe"],
            font=fontStyle2, y=225, x=100, default=3)
        self.commonCombo(
            values=["Condition2", "Artery", "Feedr", "Norm", "RRNn", "RRAn", "PosN", "PosA", "RRNe", "RRAe"],
            font=fontStyle2, y=250, x=100, default=1)
        self.commonCombo(values=["BldgType", "1Fam", "2FmCon", "Duplx", "TwnhsE", "TwnhsI"], font=fontStyle2, y=275,
                         x=100, default=2)
        self.commonCombo(
            values=["HouseStyle", "1Story", "1.5Fin", "1.5Unf", "2Story", "2.5Fin", "2.5Unf", "SFoyer", "SLvl"],
            font=fontStyle2, y=300, x=100, default=2)
        self.commonCombo(values=["OverallQual", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], font=fontStyle2,
                         y=325, x=100, default=10)
        self.commonCombo(values=["OverallCond", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], font=fontStyle2,
                         y=350, x=100, default=10)
        # --------------------------------------------------------------------------------------
        self.commonCombo(
            values=["RoofMatl", "ClyTile", "CompShg", "Membran", "Metal", "Roll", "Tar&Grv", "WdShake", "WdShngl"],
            font=fontStyle2, y=50, x=300, default=1)
        self.commonCombo(
            values=["Exterior1st", "AsbShng", "AsphShn", "BrkComm", "BrkFace", "CBlock", "CemntBd", "HdBoard",
                    "ImStucc", "MetalSd", "Other", "Plywood", "PreCast", "Stone", "Stucco", "VinylSd", "Wd Sdng",
                    "WdShing"], font=fontStyle2, y=75, x=300, default=3)
        self.commonCombo(
            values=["Exterior2nd", "AsbShng", "AsphShn", "BrkComm", "BrkFace", "CBlock", "CemntBd", "HdBoard",
                    "ImStucc", "MetalSd", "Other", "Plywood", "PreCast", "Stone", "Stucco", "VinylSd", "Wd Sdng",
                    "WdShing"], font=fontStyle2, y=100, x=300, default=5)
        self.commonCombo(values=["ExterCond", "Ex", "Gd", "TA", "Fa", "Po"], font=fontStyle2, y=125, x=300, default=4)
        self.commonCombo(values=["BsmtCond", "Ex", "Gd", "TA", "Fa", "Po", "NA"], font=fontStyle2, y=150, x=300,
                         default=4)
        self.commonCombo(values=["BsmtExposure", "Gd", "Av", "Mn", "No", "NA"], font=fontStyle2, y=175, x=300,
                         default=2)
        self.commonCombo(values=["HeatingQC", "Ex", "Gd", "TA", "Fa", "Po"], font=fontStyle2, y=200, x=300, default=4)
        self.commonCombo(values=["KitchenQual", "Ex", "Gd", "TA", "Fa", "Po"], font=fontStyle2, y=225, x=300, default=2)
        self.commonCombo(values=["FireplaceQu", "Ex", "Gd", "TA", "Fa", "Po", "NA"], font=fontStyle2, y=250, x=300,
                         default=2)
        self.commonCombo(values=["GarageType", "2Types", "Attchd", "Basment", "BuiltIn", "CarPort", "Detchd", "NA"],
                         font=fontStyle2, y=275, x=300, default=2)
        self.commonCombo(values=["GarageCond", "Ex", "Gd", "TA", "Fa", "Po", "NA"], font=fontStyle2, y=300, x=300,
                         default=2)
        self.commonCombo(values=["SaleType", "WD", "CWD", "VWD", "Nes", "COD", "Con", "ConLw", "ConLI", "ConLD", "Oth"],
                         font=fontStyle2, y=325, x=300, default=2)
        self.commonCombo(values=["SaleCondition", "Normal", "Abnormal", "AdjLand", "Alloca", "Family", "Partial"],
                         font=fontStyle2, y=350, x=300, default=2)

        # --------------------------------------------------------------------------------------
        self.labelAndEntry(text="LotFrontage", font=fontStyle, justify=RIGHT, y=50, x=600)
        self.labelAndEntry(text="LotArea", font=fontStyle, justify=RIGHT, y=100, x=600)
        self.labelAndEntry(text="YearBuilt", font=fontStyle, justify=RIGHT, y=150, x=600)
        self.labelAndEntry(text="BsmtFinSF1", font=fontStyle, justify=RIGHT, y=200, x=600)
        self.labelAndEntry(text="BsmtFinSF2", font=fontStyle, justify=RIGHT, y=250, x=600)
        self.labelAndEntry(text="1stFlrSF", font=fontStyle, justify=RIGHT, y=300, x=600)
        self.labelAndEntry(text="2ndFlrSF", font=fontStyle, justify=RIGHT, y=350, x=600)
        # --------------------------------------------------------------------------------------
        self.labelAndEntry(text="GrLivArea", font=fontStyle, justify=RIGHT, y=50, x=910)
        self.labelAndEntry(text="FullBath", font=fontStyle, justify=RIGHT, y=100, x=910)
        self.labelAndEntry(text="HalfBath", font=fontStyle, justify=RIGHT, y=150, x=910)
        self.labelAndEntry(text="BedroomAbvGr", font=fontStyle, justify=RIGHT, y=200, x=910)
        self.labelAndEntry(text="KitchenAbvGr", font=fontStyle, justify=RIGHT, y=250, x=910)
        self.labelAndEntry(text="TotRmsAbvGrd", font=fontStyle, justify=RIGHT, y=300, x=910)
        self.labelAndEntry(text="GarageCars", font=fontStyle, justify=RIGHT, y=350, x=910)

        self.labelLoad = Label(text="Load data:", font=fontStyle).place(y=502, x=100)
        self.buttonLoad = Button(bg="white", text="Open a file...", font=fontStyle2, width=15,
                                 command=self.LoadFile).place(
            y=500, x=200)
        self.buttonApply = Button(self.top, bg="white", text="Predict", font=fontStyle2, width=15,
                                  command=self.button_clickedForFile)
        self.buttonApply.place(y=500, x=350)

        self.comboAlgo = ttk.Combobox(values=[
            "KNN",
            "GaussianNB",
            "LogisticRegression",
            "LinearSVC",
            "DecisionTree",
            "RandomForest",
            "GradientBoosting",
            "AdaBoosting"], font=fontStyle2)
        self.labelAlgo = Label(text="Choose a classification algorithm:", font=fontStyle).place(y=400, x=100)
        self.comboAlgo.place(y=400, x=375)
        self.v = StringVar()
        self.top.title("House Price Prediction")
        self.top.tk_setPalette(background='#EDFFB9')
        self.top.minsize(width=1300, height=700)
        self.buttonApply2 = Button(self.top, bg="white", text="Predict", font=fontStyle2, width=15,
                                   command=self.button_clickedForUserEntry)
        self.buttonApply2.place(x=1060, y=400)
        self.top.mainloop()
        # --------------------------------------------------------------------------------------

    def LoadFile(self):
        ftypes = [('CSV Files', '*.csv'), ('All files', '*')]
        dlg = fd.Open(filetypes=ftypes)
        fl = dlg.show()

        if fl != '':
            data = open(self.fileName, "w")
            data.write(self.readFile(fl))
            data.close()

    def createUserDataFrame(self, dDF):
        for i in self.allCombo:
            print(self.allCombo[i].get())

            if i != self.allCombo[i].get():
                dDF.loc[0, i] = self.allCombo[i].get()
        for i in self.allEntry:
            print(self.allEntry[i].get())
            if self.allEntry[i].get() != '':
                dDF.loc[0, i] = self.allEntry[i].get()
        print(dDF)
        dDF.to_csv("data.csv", index=False)

    def readFile(self, filename):
        f = open(filename, "r")
        text = f.read()
        return text

    def mapComboAndClassification(self):
        comboNclassifiers = self.CnC = {}
        combos = (
            "KNN",
            "GaussianNB",
            "LogisticRegression",
            "LinearSVC",
            "DecisionTree",
            "RandomForest",
            "GradientBoosting",
            "AdaBoosting"

        )

        allClass = (
            KNN,
            GaussianNB_,
            LogisticRegression_,
            LinearSVC_,
            DecisionTree,
            RandomForest,
            GradientBoosting,
            AdaBoosting,

        )

        for i, j in zip(combos, allClass):
            self.CnC[i] = j

    def label_to_price(self, label):
        if label == 1:
            s = "less than $106,999"
        elif label == 2:
            s = "$107,000 - $178,999"
        elif label == 3:
            s = "$179,000 – $250,999"
        elif label == 4:
            s = "$251,000 – $322,999"
        elif label == 5:
            s = "$323,000 – $394,999"
        elif label == 6:
            s = "$395,000 – $466,999"
        elif label == 7:
            s = "$467,000 – $538,999"
        elif label == 8:
            s = "$539,000 – $610,999"
        elif label == 9:
            s = "$611,000 – $682,999"
        else:
            s = "more than $683,000"
        return s

    def button_clickedForUserEntry(self):
        self.mapComboAndClassification()
        c = self.CnC[self.comboAlgo.get()]()
        self.createUserDataFrame(c.c.dDF)
        opt = Optimization(self.fileName)
        opt.le_dict = c.le_dict
        opt.enc = c.enc
        opt.train = c.c.train
        data = opt.data_preparations()
        Result = c.model.predict(data)
        f = open("C:\output.txt","w")
        f.write("The cost of your house: " + self.label_to_price(Result))
        f.close()

    def button_clickedForFile(self):
        self.mapComboAndClassification()
        c = self.CnC[self.comboAlgo.get()]()
        opt = Optimization(self.fileName)
        opt.le_dict = c.le_dict
        opt.enc = c.enc
        opt.train = c.c.train
        data = opt.data_preparations()
        Result = c.model.predict(data)
        f = open("C:\output.txt", "w")
        i = 1
        for sample in Result:
            s = "The cost of your house " + str(i) + ": " + self.label_to_price(sample) +"\n"
            f.write(s)
            i = i + 1
        f.close()

app = Test()

#! /usr/bin/env python
#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Yoann ARNAUD <yarnaud@crans.org> 2009                      ##
##                                                                       ##
##                                                                       ##
## This program is free software: you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation, either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details.                          ##
##                                                                       ##
## You should have received a copy of the GNU General Public License     ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>. ##
##                                                                       ##
###########################################################################

import os, time, commands, osmapi, sys, traceback, re
import lib_translate

work  = "/data/work/analyser2/"

class analyser():

    def __init__(self, relid, force, lg):

        self._check = {}
        self._WaysJoined = []
        self._tr = lib_translate.translator(lg)
        Tr = self._tr.TranslateKey

        if "/" in relid or "." in relid:
            sys.exit(0)

        if not force and os.path.exists(os.path.join(work, "%s-res-d.html"%relid)):
            sys.exit(0)

        try:
            self._relid = int(relid)
            print "Num_OK"
        except:
            self._relid = relid
            self.error(Tr("err.InvalidNumber"))

        try:
            self.GetOsmFile()
            print "GetFile OK"
        except:
            self.error(Tr("err.WhileDL"))

        try:
            self.GetData()
            print "GetData OK"
        except:
            self.error(Tr("err.RelationNotExists"))

        try:
            self.Check()
            print "Check OK"
        except:
            traceback.print_exc(file=open(work + "error.txt","w"))
            self.error(Tr("err.WhileTesting"))

        try:
            self.WriteFiles()
            print "Write OK"
        except:
            traceback.print_exc(file=open(work + "error.txt","w"))
            self.error(Tr("err.WhileWriting"))

    def GetOsmFile(self):
        s,o = commands.getstatusoutput("wget http://api.openstreetmap.fr/api/0.6/relation/%d/full --no-cache -O "%self._relid + os.path.join(work, "%d.osm"%self._relid))

    def error(self, texte):
        #text = texte
        open(os.path.join(work, "%s.osm"%str(self._relid)), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6">\n</osm>')
        open(os.path.join(work, "%s-res-d.html"%str(self._relid)), "w").write("")
        text = u"<font color=\"#CC0000\">%s</font>"%texte
        open(os.path.join(work, "%s-res-g.html"%str(self._relid)), "w").write(text.encode("utf8"))
        sys.exit(0)

    def GetData(self, src = "api"):

        #get data
        if src=="api":
            Api = osmapi.OsmApi()
            try:
                DataRel = Api.RelationFull(self._relid)
                if not DataRel:
                    self.error("La relation n'existe pas")
            except:
                self.error("La relation n'existe pas")

        elif src=="bin":
            try:
                import Pyro.core
                bin = Pyro.core.getProxyForURI("PYROLOC://osm3/OsmBin")
                DataRel = bin.RelationFullRecur(self._relid)
                if not DataRel:
                    self.error("La relation n'existe pas")
            except:
                self.error("La relation n'existe pas")

        #
        self._relations = [ c[u'data'] for c in DataRel if c[u'type']==u'relation' ]
        self._relation  = {}
        for rel in self._relations:
            self._relation[rel[u'id']]=rel

        self._ways = [ c[u'data'] for c in DataRel if c[u'type']==u'way' ]
        self._way  = {}
        for way in self._ways:
            self._way[way[u'id']]=way

        self._nodes = [ c[u'data'] for c in DataRel if c[u'type']==u'node' ]
        self._node  = {}
        for node in self._nodes:
            self._node[node[u'id']]=node

        #Bbox
        self._mLon = float(180)
        self._mLat = float(90)
        self._MLon = float(-180)
        self._MLat = float(-90)
        for node in self._nodes:
            self._mLon = min(self._mLon,node[u'lon'])
            self._mLat = min(self._mLat,node[u'lat'])
            self._MLon = max(self._MLon,node[u'lon'])
            self._MLat = max(self._MLat,node[u'lat'])
        self._mLon -= 0.001
        self._mLat -= 0.001
        self._MLon += 0.001
        self._MLat += 0.001

    def _JoinWays(self):

        self._WaysJoined = []
        WaysATraiter = [ way[u'nd'] for way in self._ways ]
        List = []

        while True:
            Jump = False
            if len(WaysATraiter) == 0:
                return
            else:
                List = []
                List.append(WaysATraiter.pop())
                while True:
                    if Jump:
                        break
                    if len(WaysATraiter) == 0:
                        self._WaysJoined.append(List)
                        return
                    else:
                        for i in range(len(WaysATraiter)):
                            WAT = WaysATraiter[i]
                            FW = List[0]
                            LW = List[-1]
                            if WAT[-1] == FW[0]: #complete List par la gauche
                                List.insert(0,WAT)
                                WaysATraiter.remove(WAT)
                                break
                            elif WAT[0] == LW[-1]: #complete List par la droite
                                List.append(WAT)
                                WaysATraiter.remove(WAT)
                                break
                            # ways sens opposés
                            elif WAT[-1] == LW[-1]: #retourne et complete a droite
                                L = [ n for n in WAT ]
                                L.reverse()
                                List.append(L)
                                WaysATraiter.remove(WAT)
                                break
                            elif WAT[0] == FW[0]: #retourne et complete a gauche
                                L = [ n for n in WAT ]
                                L.reverse()
                                List.insert(0,L)
                                WaysATraiter.remove(WAT)
                                break
                            else:
                                if i == (len(WaysATraiter) - 1):
                                    self._WaysJoined.append(List)
                                    Jump = True


####################################################
#                    Checks                        #
####################################################

    def Check(self):

        CheckAll = self._CheckAdministrative
        CheckAll()

#####      Administrative boundaries    #####

    def _CheckAdministrative(self):
        if not self._WaysJoined:
            self._JoinWays()
        self._CheckOpen()
        self._CheckIntersect()

    def _CheckOpen(self):

        ReturnList = []
        Tr = self._tr.TranslateKey

        for List in self._WaysJoined:
            if not (List[0][0] == List[-1][-1]):
                ReturnList.append((self._node[List[0][0]][u'lon'],self._node[List[0][0]][u'lat']))
                ReturnList.append((self._node[List[-1][-1]][u'lon'],self._node[List[-1][-1]][u'lat']))

        self._check[u'open'] = (Tr('test.open'),ReturnList)


    def _CheckIntersect(self):

        self._JoinWays()
        ReturnList = []
        ReAllPoints = re.compile("[\(,][^\(,\)]*[\),]")
        Tr = self._tr.TranslateKey

        for List in self._WaysJoined:
            com = "java -classpath .:/usr/share/java/jts.jar Intersect \"LINESTRING ("
            T = []
            for way in List:
                T.append(",".join([ "%f %f"%(self._node[Nd][u'lon'],self._node[Nd][u'lat']) for Nd in way ]))
            com += ",".join(T)
            com += ")\""
            os.chdir("./jts")
            s,o = commands.getstatusoutput(com)
            os.chdir("..")
            o = o.split("\n")[0].strip()
            for point in ReAllPoints.findall(o):
                lon, lat = point[1:-1].strip().split(" ")
                ReturnList.append((float(lon),float(lat)))

        self._check[u'intersect'] = (Tr('test.intersect'),ReturnList)

####################################################
#                   Results                        #
####################################################

    def WriteFiles(self):
        self._WriteGauche()
        self._WriteDroite()
        self._WriteBubbleText()

    def _WriteGauche(self):

        Tr = self._tr.TranslateKey
        Text=[]

        JosmLink = u"http://localhost:8111/import?url=http://api.openstreetmap.fr/api/0.6/relation/%d/full"%self._relid
        Text.append(u"<div id='EditRel' >" + Tr('editrel')%u"<a class='black' href='%s' target='hiddenIframe'>JOSM</a>"%JosmLink)
        Text.append(u"</div>")

        for test in self._check:
            Res = self._check[test]
            Text.append(u'&nbsp;<img src="../www/markers/%s-l.png">'%test)
            Text.append(u"<input class='chk' id='%s' type='checkbox' name='%s' onclick=\"Toogle_Chk('%s')\">%s (%d) "%(test,test,test,Res[0],len(Res[1])))
            Text.append(u"<br>")

        fileg = open(os.path.join(work, "%d-res-g.html"%self._relid), "w")
        Text = [ l.encode("utf8") for l in Text]
        fileg.write("\n".join(Text))
        fileg.close()

    def _WriteDroite(self):

        Tags = self._relation[self._relid][u'tag']
        Text = []
        Text.append(u"<table>")
        for tag in Tags:
            Text.append(u"<tr><td class='g'>%s</td><td class='d'>%s</td></tr>"%(tag,Tags[tag]))
        Text.append(u"</table>")

        filed = open(os.path.join(work, "%d-res-d.html"%self._relid), "w")
        Text = [ l.encode("utf8") for l in Text]
        filed.writelines(Text)
        filed.close()

    def _WriteBubbleText(self):

        Tr = self._tr.TranslateKey
        for test in self._check:

            ListNodes = self._check[test][1]
            Text = []

            Text.append(u"lat\tlon\tmarker_id\ticon\ticonSize\ticonOffset\thtml\n")
            for Node in ListNodes:
                lon , lat = Node
                mid = test + "-" +  str(lon) + str(lat)
                ic = u"../www/markers/%s-b.png"%test
                e = 0.001
                JosmLink = 'http://localhost:8111/load_and_zoom?left=%f&bottom=%f&right=%f&top=%f'%(lon - e,lat - e,lon + e,lat + e)
                html = u'<div class="green" >' + Tr('editzone')%u'<a class="green" target="hiddenIframe" href="%s">JOSM</a></div>'%JosmLink
                Text.append(u"%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(lat,lon,mid,ic,'17,33','-8,-33',html))

            file = open(os.path.join(work, "%s-%s.txt"%(self._relid,test)), "w")
            Text = [ l.encode("utf8") for l in Text]
            file.writelines(Text)
            file.close()


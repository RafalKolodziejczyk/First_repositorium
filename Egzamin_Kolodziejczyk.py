# -*- coding: cp1250 -*-
#
#Generalizacja budynków egzamin IIP

import arcpy
from math import *

arcpy.env.overwriteOutput = True

#ścieżka do warstwy budynków
budynki = r'C:\Studia\AGH\PPG_II\Egzamin\Dane.shp'

#geometria
def odczyt_geom(geometria):
    try:
        lista = []
        i = 0
        for elem in geometria:
            for pkt in elem:
                if pkt:
                    lista.append([pkt.X, pkt.Y])
        i += 1
        return lista
    finally:
        del(i, elem, pkt, geometria, lista)
        
#azymut
def az(a,b):
    try:
        dy = b[1]-a[1]
        dx = b[0]-a[0]
        if dx == 0:
            czwartak = 0
            if dy<0:
                azymut=300 
            if dy>0:
                azymut=100 
        else:
            czwartak=atan(float(abs(dy))/float(abs(dx)))
            czwartak=czwartak*200/math.pi
            if dx>0:
                if dy>0:
                    azymut = czwartak
                if dy<0:
                    azymut = 400 - czwartak
                if dy==0:
                    azymut = 0
            if dx<0:
                if dy>0:
                    azymut = 200 - czwartak
                if dy<0:
                    azymut = 200 + czwartak
                if dy==0:
                    azymut = 200
        return azymut
    except Exception, err:
        arcpy.AddError("Błąd w obliczeniu azymutu")
        arcpy.AddError(sys.exc_traceback.tb_lineno)
        arcpy.AddError(err.message)
    finally:
        del(dx,dy,czwartak)
        
#liczenie kąta
def kat_az(az1,az2):
    kat_az = az2 - az1
    return(kat_az)

#usunięcie wierzchołków niespełniających kryterium tolerancji
def clear_list(lista1):
    usuwane = []
    for i1 in range(len(lista1)):
        poprzedni = i1-1
        nastepny = i1+1
        if poprzedni == -1:
            poprzedni = len(lista1)-2
        if nastepny > len(lista1)-1:
            nastepny = 1
        kat_az1=abs(kat_az(az(lista1[i1],lista1[poprzedni]),az(lista1[i1],lista1[nastepny])))
        if (kat_az1>(200-tolerancja) and kat_az1<(200+tolerancja)):
            usuwane.append(i1)
    if len(usuwane) == 0:
        return(lista1)
    else:   
        usuwane.reverse()
        for index in usuwane:
            lista1.pop(index)
        if usuwane[-1] == 0: lista1.append(lista1[0])

        return(lista1)

#odległość między punktami
def length(a,b):
    length = sqrt((a[1]-b[1])*(a[1]-b[1])+(a[0]-b[0])*(a[0]-b[0]))
    return(length)

def zasieg(dlugosc_listy,x1,x2):
    if x2 - x1 < 0:
        wynik_zasieg = dlugosc_listy - x1 - 1 + x2
    else:
        wynik_zasieg = x2 - x1 - 1
    return(wynik_zasieg)

#warunek ilości odcinanych punktów i przecinania poligonów
def create_lista_przek(lista1):
    poligon = create_arcpy_polygon(lista1)
    length1 = len(lista1)-1
    lista_przekatnych = []
    for i1 in range(len(lista1)-1):
        for i2 in range(i1+2,len(lista1)-1):
            if (((zasieg(length1,i1,i2) == k) and ((length1 - zasieg(length1,i1,i2)) >= k2)) or ((zasieg(length1,i2,i1) == k) and ((length1 - zasieg(length1,i2,i1)) >= k2))):
                if not create_arcpy_line([lista1[i1],lista1[i2]]).crosses(poligon):
                    lista_przekatnych.append([length(lista1[i1],lista1[i2]),i1,i2])                
    return(lista_przekatnych)

# najkrótsza przekątna
def znajdz_najkrotsza(lista):
    minimum = lista
    for przekatna in lista:
        if przekatna[0] < minimum[0]:
            minimum = przekatna
            
    return(minimum)

#warunek o wybraniu obiektu do odciecia
def delete_points(lista):
    najkrotsza = znajdz_najkrotsza(create_lista_przek(lista))
    object1 = range(najkrotsza[1],najkrotsza[2]+1)+[najkrotsza[1]]
    object1_1 = [lista[index] for index in object1]
    object2 = range(najkrotsza[2],len(lista)-1)+range(0,najkrotsza[1]+1)+[najkrotsza[2]]
    object2_2 = [lista[index] for index in object2]
    if create_arcpy_polygon(object2_2).area > create_arcpy_polygon(object1_1).area:
        odciete = object1_1
        glowny = object2_2
    else:
        odciete = object2_2
        glowny = object1_1
    return([glowny,odciete,najkrotsza])

#generalizacja
def generalizacja(budynek):
    ID = budynek[1]
    budynek = budynek[0]
    w = len(budynek)-1
    nr_odcietego = 1
    lista_odcietych = []
    if not len(create_lista_przek(budynek)) == 0:
        #pętla działająca tak długo, aż liczba wierzchołków wynikowego obiektu wynosi więcej niż 4
        while w > k2:
            #usuwanie zbędnych wierzchołków na bokach wielokąta
            budynek = clear_list(budynek)
            temp_budynek = budynek
            w = len(budynek)-1
            if not len(create_lista_przek(budynek)) == 0:
                if w > k2:
                        budynek,odciety,przekatna = delete_points(budynek)[0],delete_points(budynek)[1],delete_points(budynek)[2]
                        if create_arcpy_line([temp_budynek[przekatna[1]],temp_budynek[przekatna[2]]]).within(create_arcpy_polygon(temp_budynek)):    
                            odciety = [odciety,nr_odcietego,1]
                        else:
                            odciety = [odciety,nr_odcietego,0]
                        lista_odcietych.append(odciety)
                        nr_odcietego = nr_odcietego + 1
            else:
                break
            w = len(budynek)-1

    budynek = [budynek,ID]
    lista_odcietych = [lista_odcietych,ID]
    return(budynek,lista_odcietych)

#tworzenie polilinii i poligonu
def create_arcpy_line(line):
    arcpy_line = arcpy.Polyline(arcpy.Array([arcpy.Point(line[0][0],line[0][1]),arcpy.Point(line[1][0],line[1][1])]))
    return(arcpy_line)

def create_arcpy_polygon(polygon):
    arcpy_polygon = arcpy.Polygon(arcpy.Array([arcpy.Point(ppoint[0],ppoint[1]) for ppoint in polygon]))
    return(arcpy_polygon) 

#PARAMETRY PROGRAMU

tolerancja = 10 #dopuszczalne odchylenie kątowe w gradach
k=1 #liczba usunietych wierzcholkow
k2=4 #liczba punktow w wyniku
id_field_name = 'OBJECTID' #nazwa pola z ID w wejsciowym pliku

#czytanie geometrii
print('Trwa realizacja algorytmów...')
print(' ')
kursor_czytania = arcpy.da.SearchCursor(budynki, ['SHAPE@', id_field_name])
lista_budynkow = []
lista_odrzuconych = []
for row_czy in kursor_czytania:
    try:
        geometria = odczyt_geom(row_czy[0])
        lista2 = [geometria,row_czy[1]]
        lista_budynkow.append(lista2)
    except:
        lista_odrzuconych.append(row_czy[1])

#generalizacja
wynik_lista = []
wynik_lista_odcietych = []
for poligon in lista_budynkow:
    try:
        wynik_lista.append(generalizacja(poligon)[0])
        wynik_lista_odcietych.append(generalizacja(poligon)[1])
    except:
        lista_odrzuconych.append(poligon[1])

#tworzenie warstw wynikowych
print('Zapisywanie plików wynikowych...')
print(' ')
wynik_bud = arcpy.CreateFeatureclass_management(r'C:\Studia\AGH\PPG_II\Egzamin','wynik_budynki.shp','POLYGON',budynki)
wynik_bud_wyciete = arcpy.CreateFeatureclass_management(r'C:\Studia\AGH\PPG_II\Egzamin','wynik_budynki_wyciete.shp','POLYGON')
arcpy.AddField_management(wynik_bud_wyciete,'id_','SHORT')
arcpy.AddField_management(wynik_bud_wyciete,'id_s','SHORT')
arcpy.AddField_management(wynik_bud_wyciete,'In_Out','SHORT')

#tabela atrybutów
with arcpy.da.InsertCursor(wynik_bud, ['SHAPE@', id_field_name]) as cursor:
    for poligon in wynik_lista:
        cursor.insertRow([poligon[0],poligon[1]])

with arcpy.da.InsertCursor(wynik_bud_wyciete, ['SHAPE@', 'id_', 'id_s','In_Out']) as cursor:
    for budynek in wynik_lista_odcietych:
        for odciety in budynek[0]:
            id_budynku = budynek[1]
            cursor.insertRow([odciety[0],id_budynku,odciety[1],odciety[2]])

#błędy
print('Budynki z błędami: ' + str(lista_odrzuconych))

#koniec
print('Zakończono pomyślnie!')

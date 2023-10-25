# Aplikacje_Internetowe
Projekt stworzony na labolatoria Aplikacji Internetowych

Projekt polegał na stworzenie systemu komunikującego się pomiędzy elementami za pomocą http/mqtt gdzie:
 - Admin jest głównym administratorem aktywującym poszczególne elementy oraz dodający i usuwający je
 - Source zawiera programy wysyłające dane, które są sterowalne przez Admina
 - Aggregator agregujący dane z Source'ów
 - Filter filtrujący dane z Source'ów
 - Controller służacy jako kontroler do symulacji działania grzałki zawartej w Source/files/csource.py
 - Client uzyskujący dane oraz zwracający je w postaci wykresu

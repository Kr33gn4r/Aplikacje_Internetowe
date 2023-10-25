# Aplikacje_Internetowe
Projekt stworzony na labolatoria Aplikacji Internetowych

Projekt polegał na stworzenie systemu komunikującego się pomiędzy elementami za pomocą http/mqtt gdzie:
 - Admin jest głównym administratorem aktywującym poszczególne elementy oraz dodający i usuwający je
 - Source zawiera programy wysyłające dane, które są sterowalne przez Admina
 - Aggregator agreguje dane z Source'ów
 - Filter filtruje dane z Source'ów
 - Controller służy jako kontroler do symulacji działania grzałki zawartej w Source/files/csource.py
 - Client uzyskuje dane oraz zwracający je w postaci wykresu

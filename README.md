# Wsparcie pracowni 3D
Skorzystałem z socketów ZMQ, wykorzystując biblioteke pyzmq

Jeśli pyzqm nie będzie dostępne w uruchomionym blenderze, we wtyczce pojawia się przycisk, który zainstaluje ją za użytkownika. 

Na początku zaimplentowałem prosty czat, aby sprawdzić czy UI nie będzie się blokowało i czy wymiana informacji będzie przebiegać bezproblemowo. 

Na ten moment architektura wygląda tak, że: 
- Wykładowca jest ***subscriberem*** 
- Studenci są ***publisherami***

Komunikacja jest jednokierunkowa, tylko od studentów do wykładowcy. 

Przy połączeniu z wykładowcą student zobowiązany jest do podania loginu, którym będzie identyfikowany. *Tu by trzeba dodać jakąś logikę, która będzie generowała unikatowe idki*

Wykładowca przy uruchamianiu serwera, może zmienić port i ścieżkę gdzie będą zapisywane pliki .blend i screenshoty od studentów. 

Funkcja czatu nie jest zbyt rozbudowana i nie trzyma historii, tak więc jeśli wykładowca nie zdąży odczytać wiadomości od jednego studenta, a drugi mu wyśle nową wiadomość to nie jest w stanie odczytać wiadomości od pierwszego. Chciałem użyć *self.report()* do poinformowania wykładowcy o otrzymanej wiadomości. Jest taki problem, że serwer jest przywoływany co jakiś czas przez bpy.app.timers, a z tego miejsca jest problem z wywoływaniem report.

Funkcja wysyłanie plików działa, aczkolwiek na razie nie jest w żaden sposób zabezpieczone. Cały plik jest wysyłany od razu, trzeba zmienić aby plik był wysyłany w częściach.

Wysyłanie screenshotów również działa. Problem pojawił się gdy, chciałem przenieść wtyczkę do *PROPERTIES* z *3D_VIEW*, blender się crashował, więc do czasu rozwiązania problemu wtyczkę zostawiam w *3D_VIEW*

Ostatecznie przyciski do wysyłania będą zbędne u studenta, w planie jest dodanie timera, który będzie wysyłał wszystkie pliki od wykładowcy co ustawiony przedział czasowy. 

Pozostało wyświetlanie plików .png ze ścieżki podanej przez wykładowce w widoku wykładowcy. 
Czytałem, żeby wczytać je jako bpy.data.images i pozniej jakoś przerobić na tekstury, dlatego że template_preview() jest w stanie wyświetlać tylko tekstury. 


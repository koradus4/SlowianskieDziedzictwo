"""
Moduł TTS - wspiera lokalny Piper i Google Cloud TTS
"""

import subprocess
import os
from pathlib import Path
import uuid
import re
import wave
import tempfile
import logging

# Importuj skonfigurowany logger z game_logger (jeśli dostępny)
try:
    from game_logger import logger
except ImportError:
    # Fallback jeśli game_logger nie istnieje
    logger = logging.getLogger("SlowianskieDziedzictwo")

# Spróbuj zaimportować Google Cloud Storage i TTS
try:
    from google.cloud import storage
    HAS_CLOUD_STORAGE = True
except ImportError:
    HAS_CLOUD_STORAGE = False

try:
    from google.cloud import texttospeech
    HAS_CLOUD_TTS = True
except ImportError:
    HAS_CLOUD_TTS = False

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


class TTSEngine:
    """Silnik TTS - Piper (lokalnie) lub Google Cloud TTS (produkcja)"""
    
    def __init__(self, podcast_dir: Path):
        self.podcast_dir = Path(podcast_dir)
        self.piper_exe = self.podcast_dir / "piper" / "piper.exe"
        self.espeak_data = self.podcast_dir / "piper" / "espeak-ng-data"
        
        # Ścieżka do głosów lokalnych (w katalogu projektu)
        project_root = Path(__file__).parent
        self.voices_dir = project_root / "glosy_lokalnie"
        
        # Ścieżki do głosów (Piper lokalnie)
        self.glosy = {
            "jarvis": self.voices_dir / "jarvis" / "pl_PL-jarvis_wg_glos-medium.onnx",
            "meski": self.voices_dir / "meski" / "pl_PL-meski_wg_glos-medium.onnx",
            "zenski": self.voices_dir / "zenski" / "pl_PL-zenski_wg_glos-medium.onnx",
            "justyna": self.voices_dir / "justyna" / "pl_PL-justyna_wg_glos-medium.onnx",
            "darkman": self.voices_dir / "darkman" / "pl_PL-darkman-medium.onnx"
        }
        
        # Cloud Storage
        self.bucket_name = os.environ.get('GCS_BUCKET_NAME')
        self.use_cloud = self.bucket_name and HAS_CLOUD_STORAGE
        
        # Cloud TTS (Google)
        self.use_cloud_tts = HAS_CLOUD_TTS and self.use_cloud
        if self.use_cloud_tts:
            self.tts_client = texttospeech.TextToSpeechClient()
            print(f"🔊 Używam Google Cloud Text-to-Speech")
        
        if self.use_cloud:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.bucket_name)
            print(f"☁️ Używam Cloud Storage: gs://{self.bucket_name}")
        else:
            # Lokalny katalog na audio
            self.audio_dir = Path(__file__).parent / "audio"
            self.audio_dir.mkdir(exist_ok=True)
            print(f"📁 Używam lokalnego audio: {self.audio_dir}")
    
    def _zapisz_audio_cloud(self, local_path: Path) -> str:
        """Zapisuje plik audio do Cloud Storage i zwraca publiczny URL"""
        if not self.use_cloud:
            return None
        
        blob_name = f"audio/{local_path.name}"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_filename(str(local_path))
        
        # Zwróć publiczny URL (wymaga ustawienia bucket jako public)
        return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
    
    def syntezuj(self, tekst: str, glos: str = "jarvis") -> str:
        """Syntezuje tekst do pliku audio i zwraca URL (cloud) lub Path (lokalnie)"""
        
        # Cloud TTS (Google - produkcja)
        if self.use_cloud_tts:
            return self._syntezuj_google_tts(tekst)
        
        # Piper lokalnie
        if not self.piper_exe.exists():
            print(f"Brak piper.exe: {self.piper_exe}")
            return None
            
        model_path = self.glosy.get(glos)
        if not model_path or not model_path.exists():
            print(f"Brak modelu głosu: {glos}")
            return None
        
        # Lokalny plik wyjściowy
        output_file = self.audio_dir / f"{uuid.uuid4().hex}.wav"
        
        try:
            cmd = [
                str(self.piper_exe),
                "--model", str(model_path),
                "--data-dir", str(self.espeak_data),
                "--output_file", str(output_file)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            stdout, stderr = process.communicate(input=tekst.encode('utf-8'), timeout=60)
            
            if process.returncode == 0 and output_file.exists():
                return str(output_file)
            else:
                print(f"Błąd TTS: {stderr.decode('utf-8', errors='ignore')[:100]}")
                return None
                
        except Exception as e:
            print(f"Błąd syntezy: {e}")
            return None
    
    def _syntezuj_google_tts(self, tekst: str, voice_name: str = "pl-PL-Wavenet-B", pitch: float = 0.0) -> str:
        """Generuje audio przez Google Cloud TTS i zwraca publiczny URL"""
        print(f"🎙️ _syntezuj_google_tts: voice_name='{voice_name}', pitch={pitch}, tekst_len={len(tekst)}")
        logger.info(f"🎙️ _syntezuj_google_tts: voice_name='{voice_name}', pitch={pitch}, tekst_len={len(tekst)}")
        try:
            # Przygotuj żądanie
            synthesis_input = texttospeech.SynthesisInput(text=tekst)
            
            # Wybierz głos polski z dostosowanym pitch
            # Google Cloud TTS - polskie głosy Wavenet:
            # A (FEMALE wyrazista), B (MALE głęboki), C (MALE spokojny), D (FEMALE), E (FEMALE delikatna)
            gender = texttospeech.SsmlVoiceGender.MALE if "B" in voice_name or "C" in voice_name else texttospeech.SsmlVoiceGender.FEMALE
            voice = texttospeech.VoiceSelectionParams(
                language_code="pl-PL",
                name=voice_name,
                ssml_gender=gender
            )
            
            # Konfiguracja audio z custom pitch
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=pitch  # Używamy pitch z mapy
            )
            
            # Wywołaj API
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Zwróć raw bytes (do sklejania)
            return response.audio_content
            
        except Exception as e:
            print(f"❌ Błąd Google Cloud TTS: {e}")
            return None
    
    def _syntezuj_google_tts_multi(self, segments: list) -> str:
        """Generuje wielogłosowe audio i zwraca URL"""
        if not HAS_PYDUB:
            print("⚠️ Brak pydub - używam pojedynczego głosu")
            tekst_pelny = " ".join([seg[1] for seg in segments])
            return self._syntezuj_google_tts_single(tekst_pelny)
        
        try:
            audio_parts = []
            
            # Mapowanie głosów - Google Cloud ma 5 polskich Wavenet głosów:
            # A (FEMALE), B (MALE), C (MALE), D (FEMALE), E (FEMALE)
            # Używam pitch do różnicowania narrator vs NPC męski (oba B)
            voice_map = {
                "narrator": ("pl-PL-Wavenet-B", -2.0),   # Męski głęboki
                "gracz_m": ("pl-PL-Wavenet-C", 0.0),     # Męski spokojny
                "gracz_k": ("pl-PL-Wavenet-E", 1.5),     # Kobieta delikatna
                "npc_m": ("pl-PL-Wavenet-B", 1.0),       # Męski wyżej (pitch różni od narratora)
                "npc_k": ("pl-PL-Wavenet-A", 2.0)        # Kobieta wyrazista
            }
            
            # Generuj audio dla każdego segmentu
            for voice_type, tekst in segments:
                if not tekst.strip():
                    continue
                
                voice_name, pitch = voice_map.get(voice_type, ("pl-PL-Wavenet-B", -2.0))
                print(f"🎵 Segment: voice_type='{voice_type}' → voice_name='{voice_name}', pitch={pitch}, tekst_len={len(tekst)}")
                logger.info(f"🎵 Segment: voice_type='{voice_type}' → voice_name='{voice_name}', pitch={pitch}, tekst_len={len(tekst)}")
                audio_bytes = self._syntezuj_google_tts(tekst, voice_name, pitch)
                
                if audio_bytes:
                    # Konwertuj bytes na AudioSegment
                    temp_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}.mp3"
                    temp_path.write_bytes(audio_bytes)
                    segment = AudioSegment.from_mp3(str(temp_path))
                    audio_parts.append(segment)
                    temp_path.unlink()
            
            if not audio_parts:
                return None
            
            # Sklej wszystkie segmenty
            combined = sum(audio_parts)
            
            # Zapisz do pliku
            output_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}.mp3"
            combined.export(str(output_path), format="mp3")
            
            # Uploaduj do Cloud Storage
            blob_name = f"audio/{output_path.name}"
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(str(output_path))
            
            # Usuń tymczasowy plik
            output_path.unlink()
            
            # Zwróć publiczny URL
            return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
            
        except Exception as e:
            print(f"❌ Błąd wielogłosowego TTS: {e}")
            return None
    
    def _syntezuj_google_tts_single(self, tekst: str) -> str:
        """Pojedynczy głos (fallback) - zwraca URL"""
        try:
            audio_bytes = self._syntezuj_google_tts(tekst, "pl-PL-Wavenet-B")
            if not audio_bytes:
                return None
            
            # Zapisz do tymczasowego pliku
            temp_file = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}.mp3"
            temp_file.write_bytes(audio_bytes)
            
            # Uploaduj do Cloud Storage
            blob_name = f"audio/{temp_file.name}"
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(str(temp_file))
            
            # Usuń tymczasowy plik
            temp_file.unlink()
            
            # Zwróć publiczny URL
            return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
            
        except Exception as e:
            print(f"❌ Błąd Google Cloud TTS: {e}")
            return None
    
    def dostepne_glosy(self) -> list:
        """Zwraca listę dostępnych głosów"""
        return [g for g, p in self.glosy.items() if p.exists()]
    
    def syntezuj_multi_voice(self, tekst: str, plec_gracza: str = "mezczyzna") -> str:
        """
        Syntezuje tekst z wieloma głosami (Cloud TTS) lub pojedynczym (Piper)
        VERSION: 2025-12-18 22:45 - Multi-voice fixed
        """
        print(f"🎤 syntezuj_multi_voice: use_cloud_tts={self.use_cloud_tts}, tekst_len={len(tekst)}")
        logger.info(f"🎤 syntezuj_multi_voice: use_cloud_tts={self.use_cloud_tts}, tekst_len={len(tekst)}")
        
        # Cloud TTS - wielogłosowa synteza
        if self.use_cloud_tts:
            segments = self._parsuj_dialogi_cloud(tekst, plec_gracza)
            if segments:
                return self._syntezuj_google_tts_multi(segments)
            else:
                # Fallback - pojedynczy głos
                tekst_czysty = re.sub(r'\*\*[^:]+:\*\*\s*', '', tekst)
                return self._syntezuj_google_tts_single(tekst_czysty)
        
        # Piper lokalnie - wielogłosowa synteza (stary kod)
        print("🎤 Używam Piper lokalnie")
        logger.info("🎤 Używam Piper lokalnie")
        segments = self._parsuj_dialogi(tekst, plec_gracza)
        
        print(f"🎤 segments={len(segments)}")
        logger.info(f"🎤 segments={len(segments)}")
        
        if not segments:
            print("🎤 Brak segmentów, używam jarvis fallback")
            logger.info("🎤 Brak segmentów, używam jarvis fallback")
            return self.syntezuj(tekst, "jarvis")
        
        audio_files = []
        for speaker, text in segments:
            if text.strip():
                print(f"🎤 Syntetyzuję: speaker={speaker}, len={len(text)}")
                logger.info(f"🎤 Syntetyzuję: speaker={speaker}, len={len(text)}")
                audio_path = self.syntezuj(text, speaker)
                print(f"🎤 Rezultat: {audio_path}")
                logger.info(f"🎤 Rezultat: {audio_path}")
                if audio_path:
                    audio_files.append(Path(audio_path))
        
        print(f"🎤 audio_files={len(audio_files)}")
        logger.info(f"🎤 audio_files={len(audio_files)}")
        
        if not audio_files:
            print("🎤 BRAK audio_files - zwracam None!")
            logger.warning("🎤 BRAK audio_files - zwracam None!")
            return None
        
        if len(audio_files) == 1:
            result = str(audio_files[0])
            print(f"🎤 Zwracam pojedynczy plik: {result}")
            logger.info(f"🎤 Zwracam pojedynczy plik: {result}")
            return result
        
        result = str(self._sklej_audio(audio_files))
        print(f"🎤 Zwracam sklejone audio: {result}")
        logger.info(f"🎤 Zwracam sklejone audio: {result}")
        return result
    
    def _parsuj_dialogi_cloud(self, tekst: str, plec_gracza: str = "mezczyzna") -> list:
        """
        Parsuje tekst dla Cloud TTS i zwraca listę (typ_głosu, tekst).
        Format: Mówca: tekst (gwiazdki ** są już usunięte przez game_master)
        Narrator: → narrator
        Gracz: → gracz_m (mężczyzna) lub gracz_k (kobieta)
        NPC [M]: → npc_m
        NPC [K]: → npc_k
        """
        segments = []
        
        logger.info(f"🔍 CLOUD TTS _parsuj_dialogi_cloud: zaczynamy parsowanie...")
        logger.info(f"   Tekst (pierwsze 200 znaków): {tekst[:200]}")
        
        # Split tekstu na linie z oznaczeniami i bez
        lines = tekst.split('\n')
        current_speaker = "Narrator"  # Domyślny mówca
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Sprawdź czy linia zaczyna się od oznaczenia mówcy
            match = re.match(r'^([A-ZŁŚŻŹĆŃ][a-ząęółśżźćń]+(?:\s+\[[MK]\])?):(.+)', line)
            
            if match:
                # Nowy mówca - zapisz poprzedni segment
                if current_text:
                    full_text = '\n'.join(current_text).strip()
                    if full_text:
                        voice_type = self._okresl_glos_cloud(current_speaker, plec_gracza)
                        logger.info(f"   → Segment: speaker='{current_speaker}', voice={voice_type}, tekst_len={len(full_text)}")
                        segments.append((voice_type, full_text))
                
                # Nowy mówca
                current_speaker = match.group(1).strip()
                current_text = [match.group(2).strip()]
            else:
                # Kontynuacja tekstu poprzedniego mówcy lub narracja bez oznaczenia
                if not current_text:
                    # Tekst bez mówcy na początku - to narrator
                    current_speaker = "Narrator"
                current_text.append(line)
        
        # Zapisz ostatni segment
        if current_text:
            full_text = '\n'.join(current_text).strip()
            if full_text:
                voice_type = self._okresl_glos_cloud(current_speaker, plec_gracza)
                logger.info(f"   → Segment: speaker='{current_speaker}', voice={voice_type}, tekst_len={len(full_text)}")
                segments.append((voice_type, full_text))
        
        logger.info(f"   Znaleziono {len(segments)} segmentów")
        
        return segments
    
    def _okresl_glos_cloud(self, speaker: str, plec_gracza: str) -> str:
        """Określa typ głosu dla Cloud TTS na podstawie mówcy"""
        speaker_lower = speaker.lower()
        
        print(f"🔍 CLOUD TTS _okresl_glos_cloud: speaker='{speaker}', speaker_lower='{speaker_lower}', plec_gracza='{plec_gracza}'")
        logger.info(f"🔍 CLOUD TTS _okresl_glos_cloud: speaker='{speaker}', speaker_lower='{speaker_lower}', plec_gracza='{plec_gracza}'")
        
        # Określ typ głosu
        if "narrator" in speaker_lower:
            voice_type = "narrator"
            print(f"  ✅ Match: NARRATOR → narrator")
            logger.info(f"  → NARRATOR → narrator")
        elif "gracz" in speaker_lower:
            # Użyj płci gracza do wyboru głosu
            voice_type = "gracz_k" if plec_gracza == "kobieta" else "gracz_m"
            print(f"  ✅ Match: GRACZ ({plec_gracza}) → {voice_type}")
            logger.info(f"  → GRACZ ({plec_gracza}) → {voice_type}")
        elif "[k]" in speaker_lower:
            voice_type = "npc_k"
            print(f"  ✅ Match: [k] found → npc_k")
            logger.info(f"  → NPC [K] → npc_k")
        elif "[m]" in speaker_lower:
            voice_type = "npc_m"
            print(f"  ✅ Match: [m] found → npc_m")
            logger.info(f"  → NPC [M] → npc_m")
        else:
            # Inteligentne rozpoznawanie po imieniu
            zenskie_zakonczenia = ('a', 'na', 'wa', 'ka', 'ta')
            meskie_wyjatki = ('kuba', 'barnaba', 'kosma')
            
            imie_parts = speaker_lower.split()
            if len(imie_parts) > 0:
                pierwsze_slowo = imie_parts[0]
                print(f"  🔍 Fallback - sprawdzam imię NPC: '{pierwsze_slowo}'")
                logger.info(f"  → Sprawdzam imię NPC: '{pierwsze_slowo}'")
                
                if pierwsze_slowo.endswith(zenskie_zakonczenia) and pierwsze_slowo not in meskie_wyjatki:
                    voice_type = "npc_k"
                    print(f"  ✅ Końcówka '{pierwsze_slowo[-2:]}' → npc_k (KOBIETA)")
                    logger.info(f"  → NPC ŻEŃSKI (końcówka '{pierwsze_slowo[-2:]}') → npc_k")
                else:
                    voice_type = "npc_m"
                    print(f"  ✅ Brak żeńskiej końcówki → npc_m (MĘŻCZYZNA)")
                    logger.info(f"  → NPC MĘSKI → npc_m")
            else:
                # Domyślnie narrator
                voice_type = "narrator"
                print(f"  ⚠️ Fallback → narrator (brak imienia)")
                logger.info(f"  → DOMYŚLNY → narrator")
        
        print(f"  🎯 FINAL RESULT: voice_type='{voice_type}'")
        logger.info(f"  🎯 FINAL: voice_type='{voice_type}'")
        return voice_type
    
    def _parsuj_dialogi(self, tekst: str, plec_gracza: str) -> list:
        """
        Parsuje tekst i zwraca listę (głos, tekst).
        Format: Mówca: tekst (gwiazdki ** są już usunięte przez game_master)
        """
        segments = []
        
        print(f"🔍 PIPER _parsuj_dialogi: zaczynamy parsowanie...")
        print(f"   Tekst (pierwsze 200 znaków): {tekst[:200]}")
        logger.info(f"🔍 PIPER _parsuj_dialogi: zaczynamy parsowanie...")
        logger.info(f"   Tekst (pierwsze 200 znaków): {tekst[:200]}")
        
        # Split tekstu na linie z oznaczeniami i bez
        lines = tekst.split('\n')
        current_speaker = "Narrator"  # Domyślny mówca
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Sprawdź czy linia zaczyna się od oznaczenia mówcy
            match = re.match(r'^([A-ZŁŚŻŹĆŃ][a-ząęółśżźćń]+(?:\s+\[[MK]\])?):(.+)', line)
            
            if match:
                # Nowy mówca - zapisz poprzedni segment
                if current_text:
                    full_text = '\n'.join(current_text).strip()
                    if full_text:
                        print(f"   → Segment: speaker='{current_speaker}', tekst_len={len(full_text)}")
                        logger.info(f"   → Segment: speaker='{current_speaker}', tekst_len={len(full_text)}")
                        voice = self._okresl_glos(current_speaker, plec_gracza)
                        segments.append((voice, full_text))
                
                # Nowy mówca
                current_speaker = match.group(1).strip()
                current_text = [match.group(2).strip()]
            else:
                # Kontynuacja tekstu poprzedniego mówcy lub narracja bez oznaczenia
                if not current_text:
                    # Tekst bez mówcy na początku - to narrator
                    current_speaker = "Narrator"
                current_text.append(line)
        
        # Zapisz ostatni segment
        if current_text:
            full_text = '\n'.join(current_text).strip()
            if full_text:
                print(f"   → Segment: speaker='{current_speaker}', tekst_len={len(full_text)}")
                logger.info(f"   → Segment: speaker='{current_speaker}', tekst_len={len(full_text)}")
                voice = self._okresl_glos(current_speaker, plec_gracza)
                segments.append((voice, full_text))
        
        print(f"   Znaleziono {len(segments)} segmentów")
        logger.info(f"   Znaleziono {len(segments)} segmentów")
        
        return segments
    
    def _okresl_glos(self, speaker: str, plec_gracza: str) -> str:
        """Dobiera głos na podstawie mówiącego i płci"""
        speaker_lower = speaker.lower()
        
        print(f"🔍 DEBUG _okresl_glos: speaker='{speaker}', plec_gracza='{plec_gracza}'")
        logger.info(f"🔍 DEBUG _okresl_glos: speaker='{speaker}', plec_gracza='{plec_gracza}'")
        
        # Narrator - głęboki męski głos
        if 'narrator' in speaker_lower:
            logger.info(f"  → NARRATOR → jarvis")
            return 'jarvis'
        
        # Gracz - zależnie od płci
        if 'gracz' in speaker_lower:
            glos = 'zenski' if plec_gracza == 'kobieta' else 'meski'
            logger.info(f"  → GRACZ ({plec_gracza}) → {glos}")
            return glos
        
        # NPC - sprawdź oznaczenie [M]/[K] lub typowe męskie/żeńskie imiona
        if '[m]' in speaker_lower:
            logger.info(f"  → NPC [M] → darkman")
            return 'darkman'
        elif '[k]' in speaker_lower:
            logger.info(f"  → NPC [K] → justyna")
            return 'justyna'
        
        # Typowe żeńskie zakończenia imion słowiańskich
        zenskie_zakonczenia = ('a', 'na', 'wa', 'ka', 'ta')
        # Wyłączenia - męskie imiona kończące się na 'a'
        meskie_wyjatki = ('kuba', 'barnaba', 'kosma')
        
        # Sprawdź czy to NPC po imieniu
        imie_parts = speaker_lower.split()
        if len(imie_parts) > 0:
            pierwsze_slowo = imie_parts[0]
            logger.info(f"  → Sprawdzam imię: '{pierwsze_slowo}'")
            # Jeśli to typowo żeńskie imię
            if pierwsze_slowo.endswith(zenskie_zakonczenia) and pierwsze_slowo not in meskie_wyjatki:
                logger.info(f"  → NPC ŻEŃSKI (końcówka '{pierwsze_slowo[-2:]}') → justyna")
                return 'justyna'
            # Jeśli to typowo męskie (lub nie pasuje do żeńskich)
            elif not pierwsze_slowo.endswith(zenskie_zakonczenia):
                logger.info(f"  → NPC MĘSKI (brak żeńskiej końcówki) → darkman")
                return 'darkman'
        
        # Domyślnie narrator
        logger.info(f"  → DOMYŚLNY → jarvis")
        return 'jarvis'
    
    def _sklej_audio(self, audio_files: list) -> Path:
        """Skleja wiele plików WAV w jeden"""
        output_file = self.audio_dir / f"{uuid.uuid4().hex}.wav"
        
        try:
            # Otwórz wszystkie pliki i zbierz dane
            data = []
            params = None
            
            for audio_path in audio_files:
                with wave.open(str(audio_path), 'rb') as wf:
                    if params is None:
                        params = wf.getparams()
                    data.append(wf.readframes(wf.getnframes()))
            
            # Zapisz sklejony plik
            with wave.open(str(output_file), 'wb') as output:
                output.setparams(params)
                for d in data:
                    output.writeframes(d)
            
            # Usuń tymczasowe pliki
            for audio_path in audio_files:
                try:
                    audio_path.unlink()
                except:
                    pass
            
            return output_file
            
        except Exception as e:
            print(f"Błąd sklejania audio: {e}")
            # Zwróć pierwszy plik jako fallback
            return audio_files[0] if audio_files else None

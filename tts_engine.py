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
    
    def _syntezuj_google_tts(self, tekst: str, voice_name: str = "pl-PL-Wavenet-B") -> str:
        """Generuje audio przez Google Cloud TTS i zwraca publiczny URL"""
        try:
            # Przygotuj żądanie
            synthesis_input = texttospeech.SynthesisInput(text=tekst)
            
            # Wybierz głos polski z dostosowanym pitch
            # Narrator: pl-PL-Wavenet-B (męski głęboki, pitch=-2)
            # Gracz: pl-PL-Wavenet-C (męski spokojny, pitch=0)
            # NPC męski: pl-PL-Wavenet-D (męski energiczny, pitch=1)
            # NPC kobieta: pl-PL-Wavenet-A (kobieta wyrazista, pitch=2)
            gender = texttospeech.SsmlVoiceGender.MALE if "B" in voice_name or "C" in voice_name or "D" in voice_name else texttospeech.SsmlVoiceGender.FEMALE
            voice = texttospeech.VoiceSelectionParams(
                language_code="pl-PL",
                name=voice_name,
                ssml_gender=gender
            )
            
            # Ustaw pitch na podstawie głosu
            pitch_map = {
                "pl-PL-Wavenet-A": 2.0,   # Kobieta NPC - wyżej
                "pl-PL-Wavenet-B": -2.0,  # Narrator - głębiej
                "pl-PL-Wavenet-C": 0.0,   # Gracz mężczyzna - neutralnie
                "pl-PL-Wavenet-D": 1.0,   # NPC męski - lekko wyżej
                "pl-PL-Wavenet-E": 1.5    # Graczka kobieta - delikatnie wyżej
            }
            pitch = pitch_map.get(voice_name, 0.0)
            
            # Konfiguracja audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=pitch
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
            
            # Mapowanie głosów - 5 różnych głosów Google Cloud (z płcią gracza)
            voice_map = {
                "narrator": "pl-PL-Wavenet-B",  # Męski głęboki (narrator)
                "gracz_m": "pl-PL-Wavenet-C",    # Męski spokojny (bohater mężczyzna)
                "gracz_k": "pl-PL-Wavenet-E",    # Kobieta delikatna (bohaterka kobieta)
                "npc_m": "pl-PL-Wavenet-D",      # Męski energiczny (NPC mężczyzna)
                "npc_k": "pl-PL-Wavenet-A"       # Kobieta wyrazista (NPC kobieta)
            }
            
            # Generuj audio dla każdego segmentu
            for voice_type, tekst in segments:
                if not tekst.strip():
                    continue
                
                voice_name = voice_map.get(voice_type, "pl-PL-Wavenet-B")
                audio_bytes = self._syntezuj_google_tts(tekst, voice_name)
                
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
        """
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
        segments = self._parsuj_dialogi(tekst, plec_gracza)
        
        if not segments:
            return self.syntezuj(tekst, "jarvis")
        
        audio_files = []
        for speaker, text in segments:
            if text.strip():
                audio_path = self.syntezuj(text, speaker)
                if audio_path:
                    audio_files.append(Path(audio_path))
        
        if not audio_files:
            return None
        
        if len(audio_files) == 1:
            return str(audio_files[0])
        
        return str(self._sklej_audio(audio_files))
    
    def _parsuj_dialogi_cloud(self, tekst: str, plec_gracza: str = "mezczyzna") -> list:
        """
        Parsuje tekst dla Cloud TTS i zwraca listę (typ_głosu, tekst).
        **Narrator:** → narrator
        **Gracz:** → gracz_m (mężczyzna) lub gracz_k (kobieta)
        **NPC [M]:** → npc_m
        **NPC [K]:** → npc_k
        """
        segments = []
        
        # Regex: **cokolwiek:** tekst (do następnego ** lub końca)
        pattern = r'\*\*([^:]+):\*\*\s*([^*]+?)(?=\*\*|$)'
        matches = re.findall(pattern, tekst, re.DOTALL)
        
        for speaker_raw, text in matches:
            speaker = speaker_raw.strip()
            text = text.strip()
            
            if not text:
                continue
            
            # Określ typ głosu
            if "Narrator" in speaker or "narrator" in speaker:
                voice_type = "narrator"
            elif "Gracz" in speaker or "gracz" in speaker:
                # Użyj płci gracza do wyboru głosu
                voice_type = "gracz_k" if plec_gracza == "kobieta" else "gracz_m"
            elif "[K]" in speaker or "[k]" in speaker:
                voice_type = "npc_k"
            elif "[M]" in speaker or "[m]" in speaker:
                voice_type = "npc_m"
            else:
                # Domyślnie narrator
                voice_type = "narrator"
            
            segments.append((voice_type, text))
        
        return segments
    
    def _parsuj_dialogi(self, tekst: str, plec_gracza: str) -> list:
        """
        Parsuje tekst i zwraca listę (głos, tekst).
        Format: **Mówca:** tekst lub **Mówca [M/K]:** tekst
        """
        segments = []
        
        # Regex: **cokolwiek:** dowolny tekst (do następnego ** lub końca)
        pattern = r'\*\*([^:]+):\*\*\s*([^*]+?)(?=\*\*|$)'
        matches = re.findall(pattern, tekst, re.DOTALL)
        
        for speaker_raw, text in matches:
            speaker = speaker_raw.strip()
            text = text.strip()
            
            # Określ głos
            voice = self._okresl_glos(speaker, plec_gracza)
            segments.append((voice, text))
        
        return segments
    
    def _okresl_glos(self, speaker: str, plec_gracza: str) -> str:
        """Dobiera głos na podstawie mówiącego i płci"""
        speaker_lower = speaker.lower()
        
        # Narrator - głęboki męski głos
        if 'narrator' in speaker_lower:
            return 'jarvis'
        
        # Gracz - zależnie od płci
        if 'gracz' in speaker_lower:
            if plec_gracza == 'kobieta':
                return 'zenski'
            else:
                return 'meski'
        
        # NPC - sprawdź oznaczenie [M]/[K] lub typowe męskie/żeńskie imiona
        if '[m]' in speaker_lower:
            return 'darkman'  # Mężczyzna NPC
        elif '[k]' in speaker_lower:
            return 'justyna'  # Kobieta NPC
        
        # Typowe żeńskie zakończenia imion słowiańskich
        zenskie_zakonczenia = ('a', 'na', 'wa', 'ka', 'ta')
        # Wyłączenia - męskie imiona kończące się na 'a'
        meskie_wyjatki = ('kuba', 'barnaba', 'kosma')
        
        # Sprawdź czy to NPC po imieniu
        imie_parts = speaker_lower.split()
        if len(imie_parts) > 0:
            pierwsze_slowo = imie_parts[0]
            # Jeśli to typowo żeńskie imię
            if pierwsze_slowo.endswith(zenskie_zakonczenia) and pierwsze_slowo not in meskie_wyjatki:
                return 'justyna'  # Kobieta NPC
            # Jeśli to typowo męskie (lub nie pasuje do żeńskich)
            elif not pierwsze_slowo.endswith(zenskie_zakonczenia):
                return 'darkman'  # Mężczyzna NPC
        
        # Domyślnie narrator
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

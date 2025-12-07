"""
Moduł TTS - wspiera lokalny Piper i Google Cloud TTS
"""

import subprocess
import os
from pathlib import Path
import uuid
import re
import wave

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
        self.voices_dir = self.podcast_dir / "voices"
        
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
        """Generuje audio przez Google Cloud TTS z wybranym głosem i zwraca publiczny URL"""
        try:
            # Przygotuj żądanie
            synthesis_input = texttospeech.SynthesisInput(text=tekst)
            
            # Wybierz głos polski
            voice = texttospeech.VoiceSelectionParams(
                language_code="pl-PL",
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.MALE if "B" in voice_name or "C" in voice_name else texttospeech.SsmlVoiceGender.FEMALE
            )
            
            # Konfiguracja audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0
            )
            
            # Wywołaj API
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Zapisz do tymczasowego pliku
            import tempfile
            temp_file = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}.mp3"
            temp_file.write_bytes(response.audio_content)
            
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
        Syntezuje tekst z wieloma głosami (Narrator, Gracz, NPC M/K)
        Cloud TTS: parsuje tekst i generuje osobne pliki dla każdego głosu, potem skleja
        Piper lokalnie: jak było wcześniej
        """
        # Cloud TTS - multi-voice z parsowaniem
        if self.use_cloud_tts:
            return self._syntezuj_multi_voice_cloud(tekst)
        
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
    
    def _syntezuj_multi_voice_cloud(self, tekst: str) -> str:
        """Generuje multi-voice audio dla Cloud TTS"""
        try:
            # Parsuj tekst na segmenty
            segments = self._parsuj_dialogi_cloud(tekst)
            
            if not segments:
                # Fallback - cały tekst jako narrator
                return self._syntezuj_google_tts(tekst, "pl-PL-Wavenet-B")
            
            # Generuj audio dla każdego segmentu
            audio_files = []
            import tempfile
            
            for speaker_type, text_segment in segments:
                if not text_segment.strip():
                    continue
                
                # Wybierz głos na podstawie typu
                voice_map = {
                    "narrator": "pl-PL-Wavenet-B",  # Męski głęboki
                    "gracz": "pl-PL-Wavenet-C",     # Męski spokojny
                    "npc_m": "pl-PL-Wavenet-B",     # Męski (jak narrator)
                    "npc_k": "pl-PL-Wavenet-A"      # Kobieta wyrazista
                }
                
                voice_name = voice_map.get(speaker_type, "pl-PL-Wavenet-B")
                
                # Generuj audio
                temp_file = self._syntezuj_google_tts_file(text_segment, voice_name)
                if temp_file:
                    audio_files.append(temp_file)
            
            if not audio_files:
                return None
            
            # Jeśli tylko jeden segment, uploaduj go
            if len(audio_files) == 1:
                return self._zapisz_audio_cloud(audio_files[0])
            
            # Sklej pliki audio
            if not HAS_PYDUB:
                print("⚠️ Brak pydub - zwracam pierwszy plik")
                result = self._zapisz_audio_cloud(audio_files[0])
                # Usuń tymczasowe pliki
                for f in audio_files:
                    f.unlink()
                return result
            
            merged = self._sklej_audio_pydub(audio_files)
            if merged:
                cloud_url = self._zapisz_audio_cloud(merged)
                merged.unlink()
                return cloud_url
            
            return None
            
        except Exception as e:
            print(f"❌ Błąd multi-voice Cloud TTS: {e}")
            return None
    
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
        """Wymusza użycie jednego głosu (jarvis) dla całej narracji."""
        # Upraszczamy: niezależnie od mówiącego zwracamy jarvis, by uniknąć braków modeli
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
    
    def _parsuj_dialogi_cloud(self, tekst: str) -> list:
        """Parsuje tekst na segmenty dla Cloud TTS multi-voice"""
        segments = []
        
        # Regex do wyciągnięcia **Speaker:** text
        pattern = r'\*\*([^:]+):\*\*\s*([^*]+?)(?=\*\*|$)'
        matches = re.findall(pattern, tekst, re.DOTALL)
        
        for speaker, text in matches:
            speaker = speaker.strip()
            text = text.strip()
            
            # Mapuj speaker na typ
            if "Narrator" in speaker or "narrator" in speaker:
                speaker_type = "narrator"
            elif "Gracz" in speaker or "gracz" in speaker:
                speaker_type = "gracz"
            elif "[M]" in speaker or "mężczyzna" in speaker.lower():
                speaker_type = "npc_m"
            elif "[K]" in speaker or "kobieta" in speaker.lower():
                speaker_type = "npc_k"
            else:
                # Domyślnie narrator
                speaker_type = "narrator"
            
            segments.append((speaker_type, text))
        
        return segments
    
    def _syntezuj_google_tts_file(self, tekst: str, voice_name: str) -> Path:
        """Generuje tymczasowy plik MP3 dla podanego tekstu i głosu"""
        import tempfile
        
        try:
            # Konfiguracja głosu
            voice = texttospeech.VoiceSelectionParams(
                name=voice_name,
                language_code="pl-PL",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE if "B" in voice_name or "C" in voice_name else texttospeech.SsmlVoiceGender.FEMALE
            )
            
            # Konfiguracja audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0
            )
            
            # Synteza
            synthesis_input = texttospeech.SynthesisInput(text=tekst)
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Zapisz do tymczasowego pliku
            temp_file = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}.mp3"
            temp_file.write_bytes(response.audio_content)
            
            return temp_file
            
        except Exception as e:
            print(f"❌ Błąd generowania audio dla głosu {voice_name}: {e}")
            return None
    
    def _sklej_audio_pydub(self, audio_files: list) -> Path:
        """Skleja pliki MP3 używając pydub"""
        import tempfile
        
        try:
            combined = AudioSegment.empty()
            
            for audio_path in audio_files:
                segment = AudioSegment.from_mp3(str(audio_path))
                combined += segment
            
            # Zapisz sklejony plik
            output_file = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}.mp3"
            combined.export(str(output_file), format="mp3")
            
            # Usuń tymczasowe pliki
            for audio_path in audio_files:
                try:
                    audio_path.unlink()
                except:
                    pass
            
            return output_file
            
        except Exception as e:
            print(f"❌ Błąd sklejania audio pydub: {e}")
            return None

    def _zapisz_audio_cloud(self, local_path: Path) -> str:
        """Uploaduje lokalny plik MP3 do Cloud Storage i zwraca URL"""
        try:
            # Nazwa pliku w bucket
            blob_name = f"audio/{uuid.uuid4().hex}.mp3"
            
            # Upload
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(str(local_path))
            
            # Ustaw public access
            blob.make_public()
            
            # Usuń lokalny plik
            try:
                local_path.unlink()
            except:
                pass
            
            # Zwróć publiczny URL
            return blob.public_url
            
        except Exception as e:
            print(f"❌ Błąd uploadu do Cloud Storage: {e}")
            return None

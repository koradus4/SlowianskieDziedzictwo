"""
Moduł TTS - wspiera lokalny Piper i Google Cloud TTS
"""

import subprocess
import os
from pathlib import Path
import uuid
import re
import wave

# Spróbuj zaimportować Google Cloud Storage (opcjonalnie)
try:
    from google.cloud import storage
    HAS_CLOUD_STORAGE = True
except ImportError:
    HAS_CLOUD_STORAGE = False


class TTSEngine:
    """Silnik TTS - Piper (lokalnie) lub Google Cloud (produkcja)"""
    
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
    
    def syntezuj(self, tekst: str, glos: str = "jarvis") -> Path:
        """Syntezuje tekst do pliku audio"""
        if not self.piper_exe.exists():
            print(f"Brak piper.exe: {self.piper_exe}")
            return None
            
        model_path = self.glosy.get(glos)
        if not model_path or not model_path.exists():
            print(f"Brak modelu głosu: {glos}")
            return None
        
        # Unikalny plik wyjściowy (tymczasowo lokalnie, potem cloud)
        if self.use_cloud:
            # Tymczasowy plik lokalny przed uploadem
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            output_file = temp_dir / f"{uuid.uuid4().hex}.wav"
        else:
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
                # Jeśli używamy Cloud Storage, uploaduj i zwróć URL
                if self.use_cloud:
                    cloud_url = self._zapisz_audio_cloud(output_file)
                    # Usuń tymczasowy lokalny plik
                    output_file.unlink()
                    return cloud_url  # Zwróć URL zamiast Path
                else:
                    return output_file  # Lokalnie zwróć Path
            else:
                print(f"Błąd TTS: {stderr.decode('utf-8', errors='ignore')[:100]}")
                return None
                
        except Exception as e:
            print(f"Błąd syntezy: {e}")
            return None
    
    def dostepne_glosy(self) -> list:
        """Zwraca listę dostępnych głosów"""
        return [g for g, p in self.glosy.items() if p.exists()]
    
    def syntezuj_multi_voice(self, tekst: str, plec_gracza: str = "mezczyzna") -> Path:
        """
        Syntezuje tekst z wieloma głosami dla różnych postaci.
        Format tekstu: **Narrator:** tekst, **Gracz:** tekst, **NPC [M/K]:** tekst
        """
        # Parsuj tekst na segmenty z głosami
        segments = self._parsuj_dialogi(tekst, plec_gracza)
        
        if not segments:
            # Fallback - cały tekst jako narrator
            return self.syntezuj(tekst, "jarvis")
        
        # Generuj audio dla każdego segmentu
        audio_files = []
        for speaker, text in segments:
            if text.strip():
                audio_path = self.syntezuj(text, speaker)
                if audio_path:
                    audio_files.append(audio_path)
        
        if not audio_files:
            return None
        
        # Jeśli tylko jeden plik, zwróć go
        if len(audio_files) == 1:
            return audio_files[0]
        
        # Sklej wszystkie pliki WAV
        return self._sklej_audio(audio_files)
    
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

// Web Audio Engine for BeatsCloud with procedural drum machines, synths and rhythmic sequencers

/** Modo de reproducción:
 *  - 'synth' (default / demo): secuenciador procedural — funciona sin backend.
 *  - 'file': reproduce el audio REAL servido por Django (/api/track/<id>/preview/
 *    o /reproducir/). Es el modo "punto medio" para el Sprint 1: la UI es la misma,
 *    pero suena el archivo auténtico con la seguridad server-side de preview. */
export type PlaybackMode = 'synth' | 'file';

class BeatsAudioEngine {
  private mode: PlaybackMode = 'synth';
  private audioEl: HTMLAudioElement | null = null;
  private audioUrl: string | null = null;
  private ctx: AudioContext | null = null;
  private isPlaying: boolean = false;
  private currentPattern: string = 'trap';
  private bpm: number = 140;
  private timerId: number | null = null;
  private currentStep: number = 0;
  private masterGain: GainNode | null = null;
  private previewGain: GainNode | null = null; // Atenua la preescucha no adquirida (seguridad)
  private analyser: AnalyserNode | null = null;
  private onTimeUpdateCallback: ((time: number, duration: number) => void) | null = null;
  private onPlayStateChangeCallback: ((playing: boolean) => void) | null = null;
  private currentTime: number = 0;
  private duration: number = 180;
  private activeTrackId: string | null = null;

  private initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtx();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(0.7, this.ctx.currentTime);

      // Cadena de seguridad: master -> previewGain -> analyser -> destino.
      // previewGain atenúa la preescucha cuando el usuario no adquirió la pista.
      this.previewGain = this.ctx.createGain();
      this.previewGain.gain.setValueAtTime(1, this.ctx.currentTime);

      this.analyser = this.ctx.createAnalyser();
      this.analyser.fftSize = 64;

      this.masterGain.connect(this.previewGain);
      this.previewGain.connect(this.analyser);
      this.analyser.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  public getAnalyser(): AnalyserNode | null {
    return this.analyser;
  }

  public setVolume(vol: number) {
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setValueAtTime(Math.max(0, Math.min(1, vol)), this.ctx.currentTime);
    }
  }

  /**
   * Seguridad de preescucha: cuando el usuario NO adquirió la pista, se aplica
   * atenuación al master del motor (equivalente a un "tag protegido": la
   * preview suena amortiguada frente al master WAV full-band).
   */
  public setPreviewSecurityMode(isProtected: boolean) {
    if (!this.ctx || !this.previewGain) return;
    const target = isProtected ? 0.45 : 1;
    this.previewGain.gain.setTargetAtTime(target, this.ctx.currentTime, 0.05);
  }

  public setCallbacks(
    onTimeUpdate: (time: number, duration: number) => void,
    onPlayStateChange: (playing: boolean) => void
  ) {
    this.onTimeUpdateCallback = onTimeUpdate;
    this.onPlayStateChangeCallback = onPlayStateChange;
  }

  public getActiveTrackId(): string | null {
    return this.activeTrackId;
  }

  public getIsPlaying(): boolean {
    return this.isPlaying;
  }

  public getCurrentTime(): number {
    return this.currentTime;
  }

  public getDuration(): number {
    return this.duration;
  }

  public playTrack(trackId: string, pattern: string = 'trap', bpm: number = 130, duration: number = 180) {
    this.initContext();

    if (this.activeTrackId === trackId && this.isPlaying) {
      this.pause();
      return;
    }

    if (this.activeTrackId !== trackId) {
      this.activeTrackId = trackId;
      this.currentPattern = pattern;
      this.bpm = bpm;
      this.duration = duration;
      this.currentTime = 0;
      this.currentStep = 0;
    }

    this.isPlaying = true;
    if (this.onPlayStateChangeCallback) {
      this.onPlayStateChangeCallback(true);
    }

    if (this.mode === 'file' && this.audioEl) {
      // Audio real servido por Django. El volumen y la atenuación de preescucha
      // (setPreviewSecurityMode/setVolume) se aplican vía MediaStreamSource en la
      // misma cadena master -> previewGain -> analyser -> destination.
      this.audioEl.play().catch(() => {
        /* autoplay bloqueado: el usuario ya interactuó al hacer click */
      });
      return;
    }

    this.startSequencer();
  }

  /** Cambia el motor: 'file' usa el audio real de Django; 'synth' el secuenciador procedural. */
  public setPlaybackMode(mode: PlaybackMode) {
    const changed = this.mode !== mode;
    this.mode = mode;
    // Idempotente: el elemento <audio> se construye SIEMPRE que falte (no solo
    // cuando cambia el modo), para garantizar que en modo 'file' exista y suene
    // el mp3 real de Django aunque setAudioSource() se haya llamado antes.
    if (mode === 'synth' && this.audioEl) {
      this.audioEl.pause();
    } else if (mode === 'file' && !this.audioEl) {
      this.buildAudioElement();
    }
    if (!changed) return;
    if (this.isPlaying && this.activeTrackId) {
      // Re-arrancar el motor correcto sin cambiar la canción activa
      const t = this.currentTime;
      this.isPlaying = false;
      if (this.timerId !== null) {
        clearInterval(this.timerId);
        this.timerId = null;
      }
      this.isPlaying = true;
      if (this.mode === 'file' && this.audioEl) {
        this.audioEl.currentTime = Math.min(t, this.duration);
        this.audioEl.play().catch(() => {});
      } else {
        this.startSequencer();
      }
    }
  }

  public getPlaybackMode(): PlaybackMode {
    return this.mode;
  }

  /** Asigna la URL del archivo real (preview o full según seguridad server-side). */
  public setAudioSource(url: string | null) {
    this.audioUrl = url;
    if (this.audioEl) {
      if (url) {
        this.audioEl.src = url;
      } else {
        this.audioEl.removeAttribute('src');
      }
    }
  }

  private buildAudioElement() {
    const el = new Audio();
    el.crossOrigin = 'anonymous';
    el.preload = 'auto';
    if (this.audioUrl) el.src = this.audioUrl;

    // Enrutamos el elemento por la misma cadena de efectos para conservar
    // visualizer (analyser) y la atenuación de preescucha no adquirida.
    const attach = () => {
      if (!this.ctx || !this.previewGain) return;
      try {
        const srcNode = this.ctx.createMediaElementSource(el);
        srcNode.connect(this.masterGain!);
      } catch {
        /* createMediaElementSource solo permite una vez por elemento */
      }
    };
    el.addEventListener('loadedmetadata', () => {
      if (Number.isFinite(el.duration) && el.duration > 0) this.duration = el.duration;
      attach();
    });
    el.addEventListener('timeupdate', () => {
      this.currentTime = el.currentTime;
      if (this.onTimeUpdateCallback) this.onTimeUpdateCallback(this.currentTime, this.duration);
    });
    el.addEventListener('ended', () => {
      this.isPlaying = false;
      this.currentTime = 0;
      if (this.onPlayStateChangeCallback) this.onPlayStateChangeCallback(false);
    });
    this.audioEl = el;
  }

  public pause() {
    this.isPlaying = false;
    if (this.audioEl) this.audioEl.pause();
    if (this.timerId !== null) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
    if (this.onPlayStateChangeCallback) {
      this.onPlayStateChangeCallback(false);
    }
  }

  public seek(seconds: number) {
    this.currentTime = Math.max(0, Math.min(this.duration, seconds));
    if (this.mode === 'file' && this.audioEl && Number.isFinite(this.audioEl.duration)) {
      this.audioEl.currentTime = this.currentTime;
    }
    if (this.onTimeUpdateCallback) {
      this.onTimeUpdateCallback(this.currentTime, this.duration);
    }
  }

  private startSequencer() {
    if (this.timerId !== null) {
      clearInterval(this.timerId);
    }

    // 16th note interval in milliseconds: (60 / bpm / 4) * 1000
    const stepInterval = (60 / this.bpm / 4) * 1000;

    this.timerId = window.setInterval(() => {
      if (!this.isPlaying) return;

      this.step();
      this.currentTime += stepInterval / 1000;
      if (this.currentTime >= this.duration) {
        this.currentTime = 0;
      }
      if (this.onTimeUpdateCallback) {
        this.onTimeUpdateCallback(this.currentTime, this.duration);
      }
    }, stepInterval);
  }

  private step() {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;
    const step = this.currentStep % 16;
    this.currentStep++;

    switch (this.currentPattern) {
      case 'trap':
        // Kick on 0, 7, 10
        if (step === 0 || step === 7 || step === 10) this.play808Kick(now, 55);
        // Snare/Clap on 4, 12
        if (step === 4 || step === 12) this.playSnare(now);
        // Hi-hats with roll on 14, 15
        if (step % 2 === 0 || step === 14 || step === 15) this.playHiHat(now, step === 14 ? 0.3 : 0.6);
        // Melodic 808 sub/synth
        if (step === 0) this.playChords(now, [220, 261.63, 329.63]); // Am
        if (step === 8) this.playChords(now, [174.61, 220, 261.63]); // F
        break;

      case 'reggaeton':
        // Dembow rhythm: kick on 0, 4, 8, 12; snare on 3, 6, 11, 14
        if (step === 0 || step === 4 || step === 8 || step === 12) this.playKick(now);
        if (step === 3 || step === 6 || step === 11 || step === 14) this.playSnare(now, 0.9);
        if (step % 2 === 0) this.playHiHat(now, 0.4);
        if (step === 0) this.playChords(now, [196, 246.94, 293.66]); // G
        if (step === 8) this.playChords(now, [220, 261.63, 329.63]); // Am
        break;

      case 'synthwave':
        // Four on floor kick
        if (step === 0 || step === 4 || step === 8 || step === 12) this.playKick(now);
        if (step === 4 || step === 12) this.playSnare(now, 0.8, true);
        if (step % 2 === 1) this.playHiHat(now, 0.5); // offbeat hats
        // Bassline 16th note arp
        const synthNotes = [110, 110, 130.81, 110, 146.83, 110, 164.81, 146.83];
        this.playBassNote(now, synthNotes[step % 8]);
        break;

      case 'boom_bap':
        if (step === 0 || step === 6 || step === 10) this.playKick(now);
        if (step === 4 || step === 12) this.playSnare(now, 0.85);
        if (step % 2 === 0) this.playHiHat(now, 0.5);
        if (step === 0) this.playChords(now, [130.81, 164.81, 196, 246.94]); // Cmaj7
        if (step === 8) this.playChords(now, [146.83, 174.61, 220, 261.63]); // Dm7
        break;

      case 'rnb':
      case 'lofi':
      default:
        if (step === 0 || step === 10) this.play808Kick(now, 60);
        if (step === 4 || step === 12) this.playSnare(now, 0.6);
        if (step % 2 === 0) this.playHiHat(now, 0.35);
        if (step === 0) this.playChords(now, [174.61, 220, 261.63, 329.63]); // Fmaj7
        if (step === 8) this.playChords(now, [164.81, 196, 246.94, 293.66]); // Em7
        break;
    }
  }

  // Instrument synths
  private play808Kick(time: number, startFreq: number = 80) {
    if (!this.ctx || !this.masterGain) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(startFreq + 60, time);
    osc.frequency.exponentialRampToValueAtTime(32, time + 0.35);

    gain.gain.setValueAtTime(0.9, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.4);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(time);
    osc.stop(time + 0.4);
  }

  private playKick(time: number) {
    if (!this.ctx || !this.masterGain) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(140, time);
    osc.frequency.exponentialRampToValueAtTime(45, time + 0.12);

    gain.gain.setValueAtTime(0.85, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.15);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(time);
    osc.stop(time + 0.15);
  }

  private playSnare(time: number, vol: number = 0.7, reverbTail: boolean = false) {
    if (!this.ctx || !this.masterGain) return;

    // Noise component
    const bufferSize = this.ctx.sampleRate * (reverbTail ? 0.25 : 0.12);
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      output[i] = Math.random() * 2 - 1;
    }

    const whiteNoise = this.ctx.createBufferSource();
    whiteNoise.buffer = buffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'highpass';
    filter.frequency.setValueAtTime(1200, time);

    const noiseGain = this.ctx.createGain();
    noiseGain.gain.setValueAtTime(vol * 0.8, time);
    noiseGain.gain.exponentialRampToValueAtTime(0.01, time + (reverbTail ? 0.25 : 0.12));

    whiteNoise.connect(filter);
    filter.connect(noiseGain);
    noiseGain.connect(this.masterGain);

    // Body tone
    const osc = this.ctx.createOscillator();
    const oscGain = this.ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(190, time);
    osc.frequency.exponentialRampToValueAtTime(80, time + 0.08);

    oscGain.gain.setValueAtTime(vol * 0.6, time);
    oscGain.gain.exponentialRampToValueAtTime(0.01, time + 0.08);

    osc.connect(oscGain);
    oscGain.connect(this.masterGain);

    whiteNoise.start(time);
    osc.start(time);
    whiteNoise.stop(time + (reverbTail ? 0.25 : 0.12));
    osc.stop(time + 0.08);
  }

  private playHiHat(time: number, vol: number = 0.5) {
    if (!this.ctx || !this.masterGain) return;
    const bufferSize = this.ctx.sampleRate * 0.04;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * 0.8;
    }

    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'highpass';
    filter.frequency.setValueAtTime(7000, time);

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(vol * 0.4, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.04);

    noise.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    noise.start(time);
    noise.stop(time + 0.04);
  }

  private playChords(time: number, freqs: number[]) {
    if (!this.ctx || !this.masterGain) return;
    freqs.forEach((freq) => {
      if (!this.ctx || !this.masterGain) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, time);

      gain.gain.setValueAtTime(0.08, time);
      gain.gain.exponentialRampToValueAtTime(0.001, time + 0.6);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(time);
      osc.stop(time + 0.6);
    });
  }

  private playBassNote(time: number, freq: number) {
    if (!this.ctx || !this.masterGain) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(freq, time);

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(800, time);
    filter.frequency.exponentialRampToValueAtTime(200, time + 0.15);

    gain.gain.setValueAtTime(0.18, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.16);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    osc.start(time);
    osc.stop(time + 0.16);
  }
}

export const audioEngine = new BeatsAudioEngine();

import React from 'react';
import { Music2, Shield, HeartHandshake, Zap, Sparkles } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="py-8 pb-32 max-w-4xl mx-auto">
      {/* Hero */}
      <div className="rounded-3xl bg-gradient-to-r from-[#171822] via-[#20222f] to-[#171822] border border-zinc-800 p-8 sm:p-12 mb-10 shadow-xl text-center">
        <div className="w-14 h-14 rounded-2xl bg-amber-400 text-zinc-950 flex items-center justify-center mx-auto mb-4 font-black shadow-lg shadow-amber-400/20">
          <Music2 className="w-8 h-8" />
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
          Sobre <span className="text-amber-400">BeatsCloud</span>
        </h1>
        <p className="text-zinc-300 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
          Nacimos con una misión clara: democratizar el acceso a producciones musicales de nivel internacional para artistas emergentes y ofrecer una vitrina transparente y rentable para productores independientes.
        </p>
      </div>

      {/* Story & Pillars */}
      <div className="space-y-8">
        <div className="bg-[#14151e] border border-zinc-800 rounded-3xl p-6 sm:p-8">
          <h2 className="text-xl font-black text-white mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <span>El Desafío de la Música Urbana</span>
          </h2>
          <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed">
            Históricamente, los artistas independientes enfrentan grandes barreras para encontrar instrumentales de alta calidad con licencias comerciales claras y métodos de pago locales accesibles (como Webpay / Transbank en Chile). Por otro lado, los productores dedican horas en sus estudios sin una plataforma directa que valore y monetice sus creaciones sin intermediarios abusivos.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="bg-[#14151e] border border-zinc-800 rounded-3xl p-6">
            <div className="w-10 h-10 rounded-xl bg-zinc-800 text-amber-400 flex items-center justify-center mb-4">
              <Shield className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">Licenciamiento Transparente</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Cada beat adquirido en BeatsCloud otorga derechos comerciales claros para plataformas de streaming (Spotify, Apple Music, YouTube) y presentaciones en vivo, incluyendo archivos WAV 24-bit y pistas separadas (stems).
            </p>
          </div>

          <div className="bg-[#14151e] border border-zinc-800 rounded-3xl p-6">
            <div className="w-10 h-10 rounded-xl bg-zinc-800 text-amber-400 flex items-center justify-center mb-4">
              <HeartHandshake className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">Comunidad y Colaboración</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Fomentamos la retroalimentación genuina a través de comentarios, previsualización de ondas de audio, valoraciones y perfiles verificados de artistas y beatmakers de toda la región.
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-r from-amber-400/10 to-amber-500/10 border border-amber-400/30 rounded-3xl p-8 text-center">
          <h3 className="text-2xl font-black text-white mb-2">¿Listo para crear tu próximo proyecto?</h3>
          <p className="text-xs sm:text-sm text-zinc-300 max-w-lg mx-auto mb-6">
            Únete a la comunidad de creadores que están transformando la música urbana e independiente.
          </p>
          <div className="inline-flex items-center gap-2 text-xs font-bold text-amber-400">
            <Sparkles className="w-4 h-4" />
            <span>BeatsCloud — Hecho por y para músicos</span>
          </div>
        </div>
      </div>
    </div>
  );
};

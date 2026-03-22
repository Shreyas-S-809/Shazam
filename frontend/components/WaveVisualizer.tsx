"use client";

import { useRef, useMemo, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

const BAR_COUNT = 64;

interface WaveVisualizerProps {
  isActive: boolean;
  /** Live MediaStream from the microphone — drives real-time bar heights. */
  stream?: MediaStream | null;
}

/**
 * WaveScene reads live frequency data from the shared analyserRef
 * on every R3F frame and drives each bar's height + color.
 */
function WaveScene({
  isActive,
  analyserRef,
}: {
  isActive: boolean;
  analyserRef: React.MutableRefObject<AnalyserNode | null>;
}) {
  const meshRefs = useRef<(THREE.Mesh | null)[]>([]);
  // Reuse the same typed array every frame — no GC pressure
  const dataArrayRef = useRef(new Uint8Array(128));

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    const hasLive = isActive && !!analyserRef.current;

    if (hasLive) {
      // Resize buffer to match analyser if needed
      const binCount = analyserRef.current!.frequencyBinCount;
      if (dataArrayRef.current.length !== binCount) {
        dataArrayRef.current = new Uint8Array(binCount);
      }
      analyserRef.current!.getByteFrequencyData(dataArrayRef.current);
    }

    meshRefs.current.forEach((mesh, i) => {
      if (!mesh) return;

      const mat = mesh.material as THREE.MeshStandardMaterial;
      const offset = (i / BAR_COUNT) * Math.PI * 4;
      let height: number;
      let intensity = 0;

      if (hasLive) {
        // Map each bar to its frequency bin
        const binIndex = Math.floor(
          (i / BAR_COUNT) * dataArrayRef.current.length
        );
        const raw = dataArrayRef.current[binIndex] / 255;
        intensity = raw;
        // Smooth via lerp with previous frame scale (avoids jitter)
        const prevH = mesh.scale.y;
        height = prevH + (raw * 1.8 + 0.05 - prevH) * 0.35;
      } else {
        // Idle / processing: gentle sine wave animation
        const amplitude = isActive ? 0.6 : 0.28;
        const speed = isActive ? 2.0 : 1.0;
        height = (Math.sin(t * speed + offset) * 0.5 + 0.5) * amplitude + 0.06;
        intensity = height / 1.8;
      }

      mesh.scale.y = Math.max(0.04, height);
      mesh.position.y = height / 2;

      if (isActive) {
        // Bright green → yellow-green based on loudness
        const hue = 0.35 + intensity * 0.07;
        const lightness = 0.32 + intensity * 0.28;
        mat.color.setHSL(hue, 0.9, lightness);
        mat.emissive.setHSL(hue, 0.8, 0.04 + intensity * 0.18);
        mat.emissiveIntensity = 0.4 + intensity * 1.2;
      } else {
        mat.color.setHSL(0, 0, 0.12);
        mat.emissive.setHSL(0, 0, 0.01);
        mat.emissiveIntensity = 0.1;
      }
    });
  });

  const positions = useMemo(
    () =>
      Array.from(
        { length: BAR_COUNT },
        (_, i) => ((i - BAR_COUNT / 2) / BAR_COUNT) * 8
      ),
    []
  );

  return (
    <>
      <ambientLight intensity={0.2} />
      <pointLight position={[0, 4, 5]} intensity={1.0} color="#1DB954" />
      <pointLight position={[0, -3, -4]} intensity={0.4} color="#6366f1" />

      {positions.map((x, i) => (
        <mesh
          key={i}
          ref={(el) => {
            meshRefs.current[i] = el;
          }}
          position={[x, 0.1, 0]}
        >
          <boxGeometry args={[0.07, 1, 0.07]} />
          <meshStandardMaterial
            color="#1DB954"
            emissive="#0a4a20"
            emissiveIntensity={0.3}
            roughness={0.3}
            metalness={0.7}
          />
        </mesh>
      ))}
    </>
  );
}

export default function WaveVisualizer({ isActive, stream }: WaveVisualizerProps) {
  const analyserRef = useRef<AnalyserNode | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    // Tear down any existing context first
    if (ctxRef.current) {
      ctxRef.current.close();
      ctxRef.current = null;
      analyserRef.current = null;
    }

    if (!stream || !isActive) return;

    const ctx = new AudioContext();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;          // 128 frequency bins
    analyser.smoothingTimeConstant = 0.82; // smooths rapid spikes
    analyser.minDecibels = -90;
    analyser.maxDecibels = -10;

    ctx.createMediaStreamSource(stream).connect(analyser);

    ctxRef.current = ctx;
    analyserRef.current = analyser;

    return () => {
      analyser.disconnect();
      ctx.close();
      ctxRef.current = null;
      analyserRef.current = null;
    };
  }, [stream, isActive]);

  return (
    <div className="h-32 md:h-40 w-full rounded-2xl overflow-hidden glass">
      <Canvas
        camera={{ position: [0, 1.5, 4], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
      >
        <WaveScene isActive={isActive} analyserRef={analyserRef} />
      </Canvas>
    </div>
  );
}

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { Sparkles, Camera, RotateCw, Upload, Heart, Smile, Music, Hand } from 'lucide-react';
import { AnimationType, EmotionType } from '../types';

interface ThreeViewerProps {
  currentAnimation: AnimationType;
  onAnimationChange: (anim: AnimationType) => void;
  emotion?: EmotionType;
}

export const ThreeViewer: React.FC<ThreeViewerProps> = ({
  currentAnimation,
  onAnimationChange,
  emotion = 'calm',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const mixerRef = useRef<THREE.AnimationMixer | null>(null);
  const customModelRootRef = useRef<THREE.Object3D | null>(null);
  const proceduralRigRef = useRef<{
    root: THREE.Group;
    head: THREE.Group;
    hairBangs: THREE.Group;
    leftArm: THREE.Group;
    rightArm: THREE.Group;
    torso: THREE.Group;
    leftEye: THREE.Mesh;
    rightEye: THREE.Mesh;
    mouth: THREE.Mesh;
    blushL: THREE.Mesh;
    blushR: THREE.Mesh;
    cheeksMat: THREE.MeshBasicMaterial;
  } | null>(null);

  const [modelName, setModelName] = useState<string>('Хори (3D Аватар)');
  const [isAutoRotate, setIsAutoRotate] = useState<boolean>(false);
  const [loadingModel, setLoadingModel] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const animTimeRef = useRef<number>(0);
  const activeAnimRef = useRef<AnimationType>(currentAnimation);
  activeAnimRef.current = currentAnimation;

  // Build stylized procedural Anime 3D Avatar (Horimiya Hori Kyoko style: warm auburn-brown hair, school blazer/domestic sweater, expressive anime eyes)
  const buildProceduralHori = (): THREE.Group => {
    const charRoot = new THREE.Group();
    charRoot.name = 'HoriProceduralAvatar';

    // Materials
    const skinMat = new THREE.MeshToonMaterial({ color: 0xffe0bd });
    const hairMat = new THREE.MeshToonMaterial({ color: 0x8b4513 }); // Auburn chestnut hair
    const hairDarkMat = new THREE.MeshToonMaterial({ color: 0x6e360f });
    const blazerMat = new THREE.MeshToonMaterial({ color: 0x24324f }); // Navy school blazer
    const shirtMat = new THREE.MeshToonMaterial({ color: 0xf8fafc }); // White collar
    const tieMat = new THREE.MeshToonMaterial({ color: 0xef4444 }); // Red tie/ribbon
    const skirtMat = new THREE.MeshToonMaterial({ color: 0x334155 }); // Pleated grey-navy skirt
    const eyeWhiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const irisMat = new THREE.MeshBasicMaterial({ color: 0xb45309 }); // Warm amber/brown eyes
    const pupilMat = new THREE.MeshBasicMaterial({ color: 0x1e1b18 });
    const mouthMat = new THREE.MeshBasicMaterial({ color: 0xe11d48 });
    const cheeksMat = new THREE.MeshBasicMaterial({
      color: 0xfb7185,
      transparent: true,
      opacity: 0.6,
    });

    // Torso / Blazer
    const torso = new THREE.Group();
    torso.position.y = 0.85;

    const bodyGeom = new THREE.CylinderGeometry(0.18, 0.22, 0.45, 16);
    const bodyMesh = new THREE.Mesh(bodyGeom, blazerMat);
    bodyMesh.castShadow = true;
    torso.add(bodyMesh);

    // Shirt collar & ribbon
    const collarGeom = new THREE.ConeGeometry(0.12, 0.15, 3);
    collarGeom.rotateZ(Math.PI);
    const collar = new THREE.Mesh(collarGeom, shirtMat);
    collar.position.set(0, 0.16, 0.14);
    torso.add(collar);

    const ribbonGeom = new THREE.SphereGeometry(0.04, 8, 8);
    const ribbon = new THREE.Mesh(ribbonGeom, tieMat);
    ribbon.position.set(0, 0.12, 0.18);
    torso.add(ribbon);

    // Skirt
    const skirtGeom = new THREE.CylinderGeometry(0.22, 0.32, 0.3, 16);
    const skirt = new THREE.Mesh(skirtGeom, skirtMat);
    skirt.position.y = -0.32;
    torso.add(skirt);

    // Legs
    const legGeom = new THREE.CylinderGeometry(0.06, 0.05, 0.55, 12);
    const leftLeg = new THREE.Mesh(legGeom, skinMat);
    leftLeg.position.set(-0.1, -0.7, 0);
    torso.add(leftLeg);

    const rightLeg = new THREE.Mesh(legGeom, skinMat);
    rightLeg.position.set(0.1, -0.7, 0);
    torso.add(rightLeg);

    // Shoes
    const shoeGeom = new THREE.BoxGeometry(0.1, 0.07, 0.15);
    const shoeMat = new THREE.MeshToonMaterial({ color: 0x1f2937 });
    const shoeL = new THREE.Mesh(shoeGeom, shoeMat);
    shoeL.position.set(-0.1, -0.98, 0.03);
    torso.add(shoeL);
    const shoeR = new THREE.Mesh(shoeGeom, shoeMat);
    shoeR.position.set(0.1, -0.98, 0.03);
    torso.add(shoeR);

    // Head Group
    const head = new THREE.Group();
    head.position.y = 0.35;

    const headGeom = new THREE.SphereGeometry(0.24, 24, 24);
    headGeom.scale(1, 1.05, 0.95);
    const headMesh = new THREE.Mesh(headGeom, skinMat);
    headMesh.castShadow = true;
    head.add(headMesh);

    // Anime Eyes
    const eyeGeom = new THREE.SphereGeometry(0.055, 16, 16);
    eyeGeom.scale(0.8, 1.2, 0.3);

    const leftEye = new THREE.Mesh(eyeGeom, eyeWhiteMat);
    leftEye.position.set(-0.085, 0.02, 0.2);
    head.add(leftEye);

    const irisGeom = new THREE.SphereGeometry(0.04, 12, 12);
    irisGeom.scale(0.85, 1.1, 0.35);
    const leftIris = new THREE.Mesh(irisGeom, irisMat);
    leftIris.position.set(-0.085, 0.015, 0.22);
    head.add(leftIris);

    const pupilGeom = new THREE.SphereGeometry(0.02, 8, 8);
    const leftPupil = new THREE.Mesh(pupilGeom, pupilMat);
    leftPupil.position.set(-0.085, 0.015, 0.23);
    head.add(leftPupil);

    const rightEye = new THREE.Mesh(eyeGeom, eyeWhiteMat);
    rightEye.position.set(0.085, 0.02, 0.2);
    head.add(rightEye);

    const rightIris = new THREE.Mesh(irisGeom, irisMat);
    rightIris.position.set(0.085, 0.015, 0.22);
    head.add(rightIris);

    const rightPupil = new THREE.Mesh(pupilGeom, pupilMat);
    rightPupil.position.set(0.085, 0.015, 0.23);
    head.add(rightPupil);

    // Cute Cheeks / Blush
    const blushGeom = new THREE.CircleGeometry(0.04, 12);
    const blushL = new THREE.Mesh(blushGeom, cheeksMat);
    blushL.position.set(-0.13, -0.06, 0.2);
    blushL.rotation.y = -0.3;
    head.add(blushL);

    const blushR = new THREE.Mesh(blushGeom, cheeksMat);
    blushR.position.set(0.13, -0.06, 0.2);
    blushR.rotation.y = 0.3;
    head.add(blushR);

    // Mouth
    const mouthGeom = new THREE.TorusGeometry(0.03, 0.008, 8, 16, Math.PI);
    const mouth = new THREE.Mesh(mouthGeom, mouthMat);
    mouth.position.set(0, -0.1, 0.21);
    mouth.rotation.x = Math.PI;
    head.add(mouth);

    // Hair - Bangs & Long Back Hair
    const hairBangs = new THREE.Group();
    // Front bangs
    for (let i = -3; i <= 3; i++) {
      const strandGeom = new THREE.ConeGeometry(0.05, 0.22, 6);
      strandGeom.rotateX(Math.PI);
      const strand = new THREE.Mesh(strandGeom, hairMat);
      strand.position.set(i * 0.055, 0.12 - Math.abs(i) * 0.02, 0.21 + (3 - Math.abs(i)) * 0.01);
      strand.rotation.z = -i * 0.12;
      hairBangs.add(strand);
    }
    head.add(hairBangs);

    // Hair Back / Volume
    const backHairGeom = new THREE.SphereGeometry(0.28, 16, 16);
    backHairGeom.scale(1.05, 1.25, 1.15);
    const backHair = new THREE.Mesh(backHairGeom, hairMat);
    backHair.position.set(0, 0.04, -0.08);
    head.add(backHair);

    // Long strands flowing down past shoulders
    const longHairGeom = new THREE.CylinderGeometry(0.18, 0.12, 0.7, 12);
    const longHairL = new THREE.Mesh(longHairGeom, hairDarkMat);
    longHairL.position.set(-0.16, -0.28, -0.04);
    longHairL.rotation.z = -0.15;
    head.add(longHairL);

    const longHairR = new THREE.Mesh(longHairGeom, hairDarkMat);
    longHairR.position.set(0.16, -0.28, -0.04);
    longHairR.rotation.z = 0.15;
    head.add(longHairR);

    torso.add(head);

    // Left Arm (upper + forearm)
    const leftArm = new THREE.Group();
    leftArm.position.set(-0.24, 0.15, 0);

    const armGeom = new THREE.CylinderGeometry(0.045, 0.04, 0.42, 8);
    armGeom.translate(0, -0.18, 0);
    const armLMesh = new THREE.Mesh(armGeom, blazerMat);
    leftArm.add(armLMesh);

    const handGeom = new THREE.SphereGeometry(0.045, 8, 8);
    const handL = new THREE.Mesh(handGeom, skinMat);
    handL.position.set(0, -0.4, 0);
    leftArm.add(handL);
    torso.add(leftArm);

    // Right Arm (upper + forearm)
    const rightArm = new THREE.Group();
    rightArm.position.set(0.24, 0.15, 0);

    const armRMesh = new THREE.Mesh(armGeom, blazerMat);
    rightArm.add(armRMesh);

    const handR = new THREE.Mesh(handGeom, skinMat);
    handR.position.set(0, -0.4, 0);
    rightArm.add(handR);
    torso.add(rightArm);

    charRoot.add(torso);

    proceduralRigRef.current = {
      root: charRoot,
      head,
      hairBangs,
      leftArm,
      rightArm,
      torso,
      leftEye,
      rightEye,
      mouth,
      blushL,
      blushR,
      cheeksMat,
    };

    return charRoot;
  };

  // Initialize Three.js scene
  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth || 400;
    const height = containerRef.current.clientHeight || 500;

    // Scene
    const scene = new THREE.Scene();
    scene.background = null; // Transparent canvas
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(32, width / height, 0.1, 100);
    camera.position.set(0, 1.25, 3.4);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(renderer.domElement);

    // Lights (Anime Toon Lighting)
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.1);
    scene.add(ambientLight);

    const mainLight = new THREE.DirectionalLight(0xfff7ed, 2.2);
    mainLight.position.set(2.5, 4.5, 4);
    mainLight.castShadow = true;
    scene.add(mainLight);

    const rimLight = new THREE.DirectionalLight(0x60a5fa, 1.2);
    rimLight.position.set(-3, 2.5, -3);
    scene.add(rimLight);

    const pinkFillLight = new THREE.DirectionalLight(0xf472b6, 0.6);
    pinkFillLight.position.set(0, -1, 2);
    scene.add(pinkFillLight);

    // Floor platform / soft pedestal
    const platformGeom = new THREE.CylinderGeometry(0.8, 0.85, 0.04, 32);
    const platformMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.6,
      metalness: 0.2,
    });
    const platform = new THREE.Mesh(platformGeom, platformMat);
    platform.position.y = -0.15;
    platform.receiveShadow = true;
    scene.add(platform);

    const ringGeom = new THREE.RingGeometry(0.82, 0.87, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xec4899,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.4,
    });
    const ring = new THREE.Mesh(ringGeom, ringMat);
    ring.rotation.x = Math.PI / 2;
    ring.position.y = -0.13;
    scene.add(ring);

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0.85, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 1.2;
    controls.maxDistance = 6.0;
    controls.maxPolarAngle = Math.PI / 2 + 0.1;
    controlsRef.current = controls;

    // Add Initial Procedural Character
    const hori = buildProceduralHori();
    scene.add(hori);

    // Resize handling
    const handleResize = () => {
      if (!containerRef.current || !renderer || !camera) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop
    let reqId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      reqId = requestAnimationFrame(animate);
      const dt = clock.getDelta();
      animTimeRef.current += dt;
      const t = animTimeRef.current;
      const mode = activeAnimRef.current;

      // Update Mixer for imported models with clips
      if (mixerRef.current) {
        mixerRef.current.update(dt);
      }

      // Procedural animations if custom procedural avatar is active
      const rig = proceduralRigRef.current;
      if (rig && (!customModelRootRef.current || !mixerRef.current)) {
        if (mode === 'idle') {
          // Subtle breathing and organic anime posture
          rig.torso.position.y = 0.85 + Math.sin(t * 1.6) * 0.015;
          rig.head.rotation.z = Math.sin(t * 0.9) * 0.03;
          rig.head.rotation.x = Math.sin(t * 0.6) * 0.02;
          rig.hairBangs.rotation.z = Math.sin(t * 1.8) * 0.02;
          rig.leftArm.rotation.z = 0.1 + Math.sin(t * 1.2) * 0.03;
          rig.rightArm.rotation.z = -0.1 - Math.sin(t * 1.2) * 0.03;
          rig.leftArm.rotation.x = Math.sin(t * 0.8) * 0.02;
          rig.rightArm.rotation.x = Math.sin(t * 0.8) * 0.02;
        } else if (mode === 'wave') {
          // Right arm raised waving vigorously
          rig.torso.position.y = 0.85 + Math.sin(t * 3.0) * 0.01;
          rig.head.rotation.z = 0.06 + Math.sin(t * 1.5) * 0.04;
          rig.head.rotation.x = -0.05;
          rig.leftArm.rotation.z = 0.15;
          // Waving arm
          rig.rightArm.rotation.z = -1.8 + Math.sin(t * 7.0) * 0.45;
          rig.rightArm.rotation.x = -0.4;
          rig.hairBangs.rotation.z = Math.sin(t * 3.5) * 0.04;
        } else if (mode === 'dance') {
          // Dance groove: body bobbing and hips swaying
          rig.root.rotation.y = Math.sin(t * 2.5) * 0.25;
          rig.torso.position.y = 0.85 + Math.abs(Math.sin(t * 4.0)) * 0.05;
          rig.leftArm.rotation.z = 0.5 + Math.sin(t * 3.5) * 0.5;
          rig.rightArm.rotation.z = -0.5 - Math.sin(t * 3.5) * 0.5;
          rig.leftArm.rotation.x = Math.cos(t * 3.5) * 0.4;
          rig.rightArm.rotation.x = -Math.cos(t * 3.5) * 0.4;
          rig.head.rotation.z = Math.sin(t * 2.5) * 0.1;
          rig.head.rotation.y = Math.sin(t * 2.5) * 0.12;
        } else if (mode === 'happy') {
          // Bouncing happily
          rig.torso.position.y = 0.85 + Math.abs(Math.sin(t * 5.0)) * 0.08;
          rig.head.rotation.x = -0.1 + Math.sin(t * 3.0) * 0.08;
          rig.leftArm.rotation.z = 0.4 + Math.sin(t * 5.0) * 0.25;
          rig.rightArm.rotation.z = -0.4 - Math.sin(t * 5.0) * 0.25;
          rig.head.rotation.z = Math.sin(t * 4.0) * 0.06;
        }

        // Blinking
        const blinkCycle = t % 4;
        const isBlinking = blinkCycle > 3.85;
        rig.leftEye.scale.y = isBlinking ? 0.1 : 1.2;
        rig.rightEye.scale.y = isBlinking ? 0.1 : 1.2;

        // Emotion adjustment
        if (emotion === 'happy') {
          rig.cheeksMat.opacity = 0.85;
          rig.mouth.rotation.x = Math.PI; // smile
        } else if (emotion === 'angry') {
          rig.cheeksMat.opacity = 0.95;
          rig.mouth.rotation.x = 0; // pout
          rig.head.rotation.x = 0.08;
        } else if (emotion === 'thinking') {
          rig.cheeksMat.opacity = 0.4;
          rig.head.rotation.z = 0.15; // tilted head
        } else {
          rig.cheeksMat.opacity = 0.5;
        }
      }

      controls.autoRotate = isAutoRotate;
      controls.update();
      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(reqId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, []);

  // Update animation mode when prop changes
  useEffect(() => {
    activeAnimRef.current = currentAnimation;
    animTimeRef.current = 0;
  }, [currentAnimation]);

  // Handle custom model file drop or selection (.glb / .gltf / .vrm)
  const handleModelFileUpload = (file: File) => {
    if (!sceneRef.current) return;
    setLoadingModel(true);
    setLoadError(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      const contents = e.target?.result;
      if (!contents) return;

      const loader = new GLTFLoader();
      loader.parse(
        contents,
        '',
        (gltf) => {
          const scene = sceneRef.current!;
          // Remove previous custom model or procedural rig
          if (customModelRootRef.current) {
            scene.remove(customModelRootRef.current);
          }
          if (proceduralRigRef.current) {
            scene.remove(proceduralRigRef.current.root);
          }

          const model = gltf.scene;
          model.traverse((obj) => {
            if ((obj as THREE.Mesh).isMesh) {
              const mesh = obj as THREE.Mesh;
              mesh.castShadow = true;
              mesh.receiveShadow = true;
              // Hair alpha test fix from model_viewer.py
              const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
              mats.forEach((m: any) => {
                if (m.map && m.transparent !== false) {
                  m.alphaTest = 0.4;
                  m.transparent = false;
                  m.depthWrite = true;
                  m.side = THREE.DoubleSide;
                  m.needsUpdate = true;
                }
              });
            }
          });

          // Scale & fit into camera frame
          const box = new THREE.Box3().setFromObject(model);
          const size = box.getSize(new THREE.Vector3());
          const center = box.getCenter(new THREE.Vector3());
          const maxDim = Math.max(size.x, size.y, size.z);
          const s = 1.7 / (maxDim || 1);
          model.scale.set(s, s, s);
          model.position.sub(center.multiplyScalar(s));
          model.position.y += 0.85;

          scene.add(model);
          customModelRootRef.current = model;

          // Check for built-in animations in the GLTF
          if (gltf.animations && gltf.animations.length > 0) {
            const mixer = new THREE.AnimationMixer(model);
            const action = mixer.clipAction(gltf.animations[0]);
            action.play();
            mixerRef.current = mixer;
          }

          setModelName(file.name);
          setLoadingModel(false);
        },
        (error) => {
          console.error('Error loading 3D file:', error);
          setLoadError('Не удалось загрузить 3D модель: формат не поддерживается');
          setLoadingModel(false);
        }
      );
    };
    reader.readAsArrayBuffer(file);
  };

  const resetCamera = () => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(0, 1.25, 3.4);
      controlsRef.current.target.set(0, 0.85, 0);
      controlsRef.current.update();
    }
  };

  return (
    <div
      id="three-viewer-container"
      className="relative w-full h-full min-h-[380px] lg:min-h-[520px] rounded-2xl overflow-hidden bg-gradient-to-b from-slate-900/90 to-slate-950/95 border border-slate-800 shadow-2xl flex flex-col justify-between"
    >
      {/* Top Bar / Model Status */}
      <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700/60 shadow-lg pointer-events-auto">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-semibold text-slate-200">{modelName}</span>
        </div>

        <div className="flex items-center gap-2 pointer-events-auto">
          <button
            id="btn-auto-rotate"
            onClick={() => setIsAutoRotate(!isAutoRotate)}
            title="Автоповорот"
            className={`p-2 rounded-xl border backdrop-blur-md transition-all ${
              isAutoRotate
                ? 'bg-rose-500/20 border-rose-500/60 text-rose-300'
                : 'bg-slate-900/70 border-slate-700/60 text-slate-300 hover:text-white hover:bg-slate-800/80'
            }`}
          >
            <RotateCw className={`w-4 h-4 ${isAutoRotate ? 'animate-spin' : ''}`} />
          </button>

          <button
            id="btn-reset-cam"
            onClick={resetCamera}
            title="Сбросить камеру"
            className="p-2 rounded-xl bg-slate-900/70 border border-slate-700/60 text-slate-300 hover:text-white hover:bg-slate-800/80 backdrop-blur-md transition-all"
          >
            <Camera className="w-4 h-4" />
          </button>

          <label
            id="btn-upload-model"
            title="Загрузить свою 3D модель (.glb, .vrm)"
            className="p-2 rounded-xl bg-slate-900/70 border border-slate-700/60 text-slate-300 hover:text-rose-400 hover:bg-slate-800/80 backdrop-blur-md cursor-pointer transition-all flex items-center gap-1.5"
          >
            <Upload className="w-4 h-4" />
            <span className="text-xs font-medium hidden sm:inline">3D файл</span>
            <input
              type="file"
              accept=".glb,.gltf,.vrm"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  handleModelFileUpload(e.target.files[0]);
                }
              }}
            />
          </label>
        </div>
      </div>

      {/* 3D WebGL Canvas Host */}
      <div
        ref={containerRef}
        className="w-full h-full flex-1 cursor-grab active:cursor-grabbing"
      />

      {/* Loading or Error notification */}
      {loadingModel && (
        <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm flex flex-col items-center justify-center gap-3 z-20">
          <div className="w-8 h-8 border-2 border-rose-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-rose-200">Импорт 3D модели...</p>
        </div>
      )}

      {loadError && (
        <div className="absolute bottom-16 left-4 right-4 p-2.5 rounded-xl bg-red-950/80 border border-red-800/60 text-red-200 text-xs text-center z-10 backdrop-blur-md">
          {loadError}
        </div>
      )}

      {/* Animation Control Bar */}
      <div className="absolute bottom-4 left-4 right-4 z-10 flex flex-wrap items-center justify-between gap-2 p-2 rounded-2xl bg-slate-900/85 backdrop-blur-md border border-slate-800/80 shadow-xl">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 pl-2">
          <Sparkles className="w-3.5 h-3.5 text-rose-400" />
          <span className="font-medium hidden sm:inline">Анимации:</span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            id="anim-idle"
            onClick={() => onAnimationChange('idle')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              currentAnimation === 'idle'
                ? 'bg-rose-500 text-white shadow-md shadow-rose-500/30'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
          >
            <span>😴</span>
            <span>Покой</span>
          </button>

          <button
            id="anim-wave"
            onClick={() => onAnimationChange('wave')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              currentAnimation === 'wave'
                ? 'bg-rose-500 text-white shadow-md shadow-rose-500/30'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
          >
            <Hand className="w-3.5 h-3.5" />
            <span>Машет</span>
          </button>

          <button
            id="anim-dance"
            onClick={() => onAnimationChange('dance')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              currentAnimation === 'dance'
                ? 'bg-rose-500 text-white shadow-md shadow-rose-500/30'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
          >
            <Music className="w-3.5 h-3.5" />
            <span>Танец</span>
          </button>

          <button
            id="anim-happy"
            onClick={() => onAnimationChange('happy')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              currentAnimation === 'happy'
                ? 'bg-rose-500 text-white shadow-md shadow-rose-500/30'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
          >
            <Smile className="w-3.5 h-3.5" />
            <span>Радость</span>
          </button>
        </div>
      </div>
    </div>
  );
};

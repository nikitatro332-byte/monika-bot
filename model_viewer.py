import sys
import os
import threading
import http.server
import socketserver

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-webgl --ignore-gpu-blocklist --enable-unsafe-swiftshader"

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

# ========== ПОИСК МОДЕЛИ ==========
MODEL = None
for f in os.listdir('.'):
    if f.lower().endswith(('.vrm', '.glb')):
        MODEL = f
        break

if not MODEL:
    print("❌ Модели не найдены!")
    sys.exit(1)

is_vrm = MODEL.lower().endswith('.vrm')
print(f"📂 Модель: {MODEL} ({'VRM' if is_vrm else 'GLB'})")

# ========== ЧИТАЕМ JS-БИБЛИОТЕКИ В СТРОКИ ==========
vendor = os.path.join(os.path.abspath('.'), '_vendor')
with open(os.path.join(vendor, 'three.min.js'), 'r', encoding='utf-8') as f:
    three_js = f.read()
with open(os.path.join(vendor, 'controls', 'OrbitControls.js'), 'r', encoding='utf-8') as f:
    orbit_js = f.read()
with open(os.path.join(vendor, 'loaders', 'GLTFLoader.js'), 'r', encoding='utf-8') as f:
    gltf_js = f.read()
print(f"📦 three.js: {len(three_js)} байт, GLTFLoader: {len(gltf_js)} байт")

# ========== ЛОКАЛЬНЫЙ HTTP-СЕРВЕР (только для модели) ==========
PORT = 18765
server_dir = os.path.abspath('.')

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=server_dir, **kwargs)
    def log_message(self, format, *args):
        pass

httpd = socketserver.TCPServer(("", PORT), QuietHandler)
httpd.daemon_threads = True
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()

model_url = f"http://127.0.0.1:{PORT}/{MODEL}"

# ========== ГЕНЕРИРУЕМ HTML С ВСТРОЕННЫМИ СКРИПТАМИ ==========
html_path = os.path.join(server_dir, '_viewer_temp.html')

if is_vrm:
    vrm_load = """
        var vrm = gltf.userData.vrm;
        scene.add(vrm.scene);
        var box = new THREE.Box3().setFromObject(vrm.scene);
        var size = box.getSize(new THREE.Vector3());
        var center = box.getCenter(new THREE.Vector3());
        var s = 0.5 / Math.max(size.x, size.y, size.z);
        vrm.scene.scale.set(s, s, s);
        vrm.scene.position.sub(center.multiplyScalar(s));
"""
else:
    vrm_load = """
        scene.add(gltf.scene);
        var box = new THREE.Box3().setFromObject(gltf.scene);
        var size = box.getSize(new THREE.Vector3());
        var center = box.getCenter(new THREE.Vector3());
        var maxDim = Math.max(size.x, size.y, size.z);
        var s = 1.7 / maxDim;
        gltf.scene.scale.set(s, s, s);
        gltf.scene.position.sub(center.multiplyScalar(s));
        // Чиним мерцающие волосы — alphaTest + отключаем depthWrite
        gltf.scene.traverse(function(obj) {
            if (obj.isMesh && obj.material) {
                var mats = Array.isArray(obj.material) ? obj.material : [obj.material];
                mats.forEach(function(m) {
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
        // Наводим камеру на центр модели
        controls.target.set(0, 0, 0);
        camera.position.set(0, 0, maxDim * 2.5 / s);
        camera.near = 0.01;
        camera.far = 1000;
        camera.updateProjectionMatrix();

        // ===== АНИМАЦИЯ =====
        var modelRoot = gltf.scene;
        var mixer = new THREE.AnimationMixer(modelRoot);
        var clips = gltf.animations;
        var currentAction = null;
        var allBones = [];
        modelRoot.traverse(function(obj) {
            if (obj.isBone) {
                allBones.push(obj);
            }
        });

        log('bones: ' + allBones.length);
        // Дамп имён костей в консоль
        allBones.forEach(function(b) { console.log('BONE: ' + b.name + ' pos=' + JSON.stringify({x:b.position.x.toFixed(2),y:b.position.y.toFixed(2),z:b.position.z.toFixed(2)})); });

        // Встроенные анимации из GLB
        if (clips && clips.length > 0) {
            log('animations: ' + clips.length);
            clips.forEach(function(c) { console.log('CLIP: ' + c.name); });
        }

        // Ищем кости по части имени
        function findBone(part) {
            var pl = part.toLowerCase();
            for (var i = 0; i < allBones.length; i++) {
                if (allBones[i].name.toLowerCase().indexOf(pl) >= 0) return allBones[i];
            }
            return null;
        }

        // Автоопределение костей по позиции в скелете
        var headBone = findBone('c_head');
        var spineBone = findBone('c_spine') || findBone('c_chest');
        var leftArm = findBone('l_upperarm') || findBone('l_shoulder');
        var rightArm = findBone('r_upperarm') || findBone('r_shoulder');

        // Второй скелет (суффикс _1)
        var headBone2 = findBone('c_head_1');
        var spineBone2 = findBone('c_spine_1') || findBone('c_chest_1');
        var leftArm2 = findBone('l_upperarm_1') || findBone('l_shoulder_1');
        var rightArm2 = findBone('r_upperarm_1') || findBone('r_shoulder_1');

        // Собираем пары костей (основная + дубликат)
        var headBones = [headBone, headBone2].filter(Boolean);
        var spineBones = [spineBone, spineBone2].filter(Boolean);
        var leftArms = [leftArm, leftArm2].filter(Boolean);
        var rightArms = [rightArm, rightArm2].filter(Boolean);

        log('head:' + (headBone?headBone.name:'NO') + ' spine:' + (spineBone?spineBone.name:'NO') + ' L:' + (leftArm?leftArm.name:'NO') + ' R:' + (rightArm?rightArm.name:'NO') + ' | head2:' + (headBone2?headBone2.name:'NO') + ' L2:' + (leftArm2?leftArm2.name:'NO') + ' R2:' + (rightArm2?rightArm2.name:'NO'));

        // Сохраняем начальные позиции всех костей
        var initialRotations = {};
        var initialPositions = {};
        var initialScales = {};
        allBones.forEach(function(b) {
            initialRotations[b.name] = { x: b.rotation.x, y: b.rotation.y, z: b.rotation.z };
            initialPositions[b.name] = { x: b.position.x, y: b.position.y, z: b.position.z };
            initialScales[b.name] = { x: b.scale.x, y: b.scale.y, z: b.scale.z };
        });
        var initialModelPos = { x: modelRoot.position.x, y: modelRoot.position.y, z: modelRoot.position.z };
        var initialModelRot = { x: modelRoot.rotation.x, y: modelRoot.rotation.y, z: modelRoot.rotation.z };

        function resetAll() {
            allBones.forEach(function(b) {
                var r = initialRotations[b.name];
                var p = initialPositions[b.name];
                var sc = initialScales[b.name];
                if (r) b.rotation.set(r.x, r.y, r.z);
                if (p) b.position.set(p.x, p.y, p.z);
                if (sc) b.scale.set(sc.x, sc.y, sc.z);
            });
            modelRoot.position.set(initialModelPos.x, initialModelPos.y, initialModelPos.z);
            modelRoot.rotation.set(initialModelRot.x, initialModelRot.y, initialModelRot.z);
        }

        window.playAnim = function(name) {
            if (currentAction) {
                currentAction.fadeOut(0.3);
                currentAction = null;
            }
            resetAll();
            window._animTime = 0;
            if (clips && clips.length > 0) {
                var clip = clips.find(function(c) { return c.name.toLowerCase().indexOf(name.toLowerCase()) >= 0; });
                if (clip) {
                    currentAction = mixer.clipAction(clip);
                    currentAction.reset().fadeIn(0.3).play();
                    log('playing: ' + clip.name);
                    window._currentMode = name;
                    return;
                }
            }
            window._currentMode = name;
            log('mode: ' + name);
        };

        window._currentMode = 'idle';
        window._animTime = 0;

        function proceduralAnim(dt) {
            window._animTime += dt;
            var t = window._animTime;
            var mode = window._currentMode;

            if (mode === 'idle') {
                spineBones.forEach(function(b) { b.scale.y = initialScales[b.name].y + Math.sin(t * 1.5) * 0.02; });
                headBones.forEach(function(b) {
                    b.rotation.z = initialRotations[b.name].z + Math.sin(t * 0.8) * 0.05;
                    b.rotation.x = initialRotations[b.name].x + Math.sin(t * 0.5) * 0.03;
                });
                leftArms.forEach(function(b) { b.rotation.z = initialRotations[b.name].z + 0.1 + Math.sin(t * 0.7) * 0.03; });
                rightArms.forEach(function(b) { b.rotation.z = initialRotations[b.name].z - 0.1 - Math.sin(t * 0.7) * 0.03; });
            }
            else if (mode === 'wave') {
                rightArms.forEach(function(b) {
                    b.rotation.z = initialRotations[b.name].z - 1.2 + Math.sin(t * 4) * 0.3;
                    b.rotation.x = initialRotations[b.name].x - 0.3;
                });
                headBones.forEach(function(b) { b.rotation.z = initialRotations[b.name].z + Math.sin(t * 0.8) * 0.05; });
            }
            else if (mode === 'dance') {
                modelRoot.rotation.y = initialModelRot.y + Math.sin(t * 2) * 0.3;
                leftArms.forEach(function(b) { b.rotation.z = initialRotations[b.name].z + 0.5 + Math.sin(t * 3) * 0.4; });
                rightArms.forEach(function(b) { b.rotation.z = initialRotations[b.name].z - 0.5 - Math.sin(t * 3) * 0.4; });
                headBones.forEach(function(b) {
                    b.rotation.z = initialRotations[b.name].z + Math.sin(t * 2) * 0.1;
                    b.rotation.y = initialRotations[b.name].y + Math.sin(t * 2) * 0.1;
                });
                spineBones.forEach(function(b) { b.scale.y = initialScales[b.name].y + Math.sin(t * 4) * 0.03; });
            }
            else if (mode === 'happy') {
                modelRoot.position.y = initialModelPos.y + Math.abs(Math.sin(t * 3)) * 0.1;
                headBones.forEach(function(b) { b.rotation.x = initialRotations[b.name].x - 0.1 + Math.sin(t * 2) * 0.05; });
                leftArms.forEach(function(b) { b.rotation.z = initialRotations[b.name].z + 0.3 + Math.sin(t * 3) * 0.2; });
                rightArms.forEach(function(b) { b.rotation.z = initialRotations[b.name].z - 0.3 - Math.sin(t * 3) * 0.2; });
            }
        }

        var clock = new THREE.Clock();
        window._mixer = mixer;
        window._proceduralAnim = proceduralAnim;
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ margin:0; overflow:hidden; background:transparent; }}
    canvas {{ display:block; }}
    #err {{ display:none; position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#ff6b6b;font-size:13px;text-align:center;font-family:sans-serif;max-width:80%; }}
    #dbg {{ position:absolute;top:2px;left:2px;color:#00ff00;font-size:10px;font-family:monospace;pointer-events:none;z-index:999; }}
</style>
</head>
<body>
<div id="err"></div>
<div id="dbg">init</div>
<script>
{three_js}
</script>
<script>
{orbit_js}
</script>
<script>
{gltf_js}
</script>
<script>
var dbg = document.getElementById('dbg');
function log(msg) {{ dbg.textContent = msg; }}

log('THREE version: ' + THREE.REVISION);

var scene = new THREE.Scene();
scene.background = null;

var camera = new THREE.PerspectiveCamera(30, 400/520, 0.1, 100);
camera.position.set(0, 1.5, 3.5);

var renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
renderer.setSize(400, 520);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.appendChild(renderer.domElement);
log('renderer OK');

var light = new THREE.DirectionalLight(0xffffff, 2);
light.position.set(3, 5, 5);
scene.add(light);
scene.add(new THREE.AmbientLight(0xffffff, 0.8));

var controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.8, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.enableZoom = false;
controls.enablePan = false;
controls.update();

var loader = new THREE.GLTFLoader();
log('loading model...');

loader.load(
    '{model_url}',
    function(gltf) {{
        log('LOADED children=' + gltf.scene.children.length);
        {vrm_load}
        controls.update();
        log('added to scene');
    }},
    function(progress) {{
        if (progress.total) {{
            log('progress ' + Math.round(progress.loaded / progress.total * 100) + '%');
        }}
    }},
    function(error) {{
        log('ERROR: ' + (error.message || error));
        var div = document.getElementById('err');
        div.textContent = 'ERROR: ' + (error.message || error);
        div.style.display = 'block';
    }}
);

var clock = new THREE.Clock();

function anim() {{
    requestAnimationFrame(anim);
    var dt = clock.getDelta();
    if (window._mixer) window._mixer.update(dt);
    if (window._proceduralAnim) window._proceduralAnim(dt);
    controls.update();
    renderer.render(scene, camera);
}}
anim();
log('anim started');
</script>
</body>
</html>"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

viewer_url = f"http://127.0.0.1:{PORT}/_viewer_temp.html"
print(f"🌐 Viewer: {viewer_url}")


class ModelWin(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 520)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.view = QWebEngineView()
        self.view.setStyleSheet("background: transparent; border: none;")

        page = QWebEnginePage(self.view)
        page.setBackgroundColor(Qt.GlobalColor.transparent)
        self.view.setPage(page)

        profile = QWebEngineProfile.defaultProfile()
        profile.settings().setAttribute(profile.settings().WebAttribute.WebGLEnabled, True)
        profile.settings().setAttribute(profile.settings().WebAttribute.JavascriptEnabled, True)
        profile.settings().setAttribute(profile.settings().WebAttribute.LocalContentCanAccessRemoteUrls, True)
        profile.settings().setAttribute(profile.settings().WebAttribute.LocalContentCanAccessFileUrls, True)

        settings = page.settings()
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(settings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True)

        page.javaScriptConsoleMessage = self.js_log
        page.load(QUrl(viewer_url))
        layout.addWidget(self.view)
        self.show()

    def js_log(self, level, message, line, source):
        print(f"🖥️ JS: {message}")


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Хори Кёко")
        self.setGeometry(100, 100, 250, 150)
        self.setStyleSheet("background: #0d0d11; border-radius: 12px;")

        c = QWidget()
        self.setCentralWidget(c)
        l = QVBoxLayout(c)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        l.addWidget(QLabel("💖 Хори Кёко", alignment=Qt.AlignmentFlag.AlignCenter,
                           styleSheet="color:#007aff;font-size:24px;font-weight:bold;"))

        btn = QPushButton("👁️ Показать")
        btn.setStyleSheet(
            "QPushButton{background:#007aff;color:white;border:none;border-radius:10px;padding:12px;font-size:14px;font-weight:bold;}QPushButton:hover{background:#0055cc;}")
        btn.clicked.connect(self.show_model)
        l.addWidget(btn)

        btn2 = QPushButton("❌ Скрыть")
        btn2.setStyleSheet(
            "QPushButton{background:#ff3b30;color:white;border:none;border-radius:10px;padding:8px;font-size:13px;}QPushButton:hover{background:#cc0000;}")
        btn2.clicked.connect(self.hide_model)
        l.addWidget(btn2)

        # Кнопки анимаций
        anim_label = QLabel("🎭 Анимации:", alignment=Qt.AlignmentFlag.AlignCenter,
                            styleSheet="color:#8e8e93;font-size:12px;margin-top:8px;")
        l.addWidget(anim_label)

        anim_row = QHBoxLayout()
        for name, label in [("idle", "😴 Idle"), ("wave", "👋 Машет"), ("dance", "💃 Танец"), ("happy", "😊 Радость")]:
            b = QPushButton(label)
            b.setStyleSheet(
                "QPushButton{background:#2c2c3e;color:#aaa;border:1px solid #444;border-radius:8px;padding:6px;font-size:11px;}QPushButton:hover{background:#3c3c4e;color:white;}")
            b.clicked.connect(lambda checked, n=name: self.play_anim(n))
            anim_row.addWidget(b)
        anim_container = QWidget()
        anim_container.setLayout(anim_row)
        l.addWidget(anim_container)

        self.status = QLabel("Модель: скрыта", alignment=Qt.AlignmentFlag.AlignCenter,
                             styleSheet="color:#8e8e93;font-size:12px;")
        l.addWidget(self.status)

        self.model = ModelWin()
        self.model.hide()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1000)

    def show_model(self):
        self.model.show()
        self.status.setText("✅ Модель: показана")
        self.update_position()

    def hide_model(self):
        self.model.hide()
        self.status.setText("❌ Модель: скрыта")

    def play_anim(self, name):
        self.model.view.page().runJavaScript(f"window.playAnim && window.playAnim('{name}');")
        self.status.setText(f"🎭 Анимация: {name}")

    def update_position(self):
        if self.model.isVisible():
            s = self.screen().geometry()
            self.model.move(s.width() - self.model.width() - 10, s.height() - self.model.height())


app = QApplication(sys.argv)
w = MainWin()
w.show()
QTimer.singleShot(1000, w.show_model)
sys.exit(app.exec())

import * as THREE from '/node_modules/three/build/three.module.js';
import { OrbitControls } from '/node_modules/three/examples/jsm/controls/OrbitControls.js';

// Scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0xf0f0f0);
document.getElementById('container').appendChild(renderer.domElement);

// Lighting
//const ambientLight = new THREE.AmbientLight(0x404040);
const ambientLight = new THREE.AmbientLight(0xffffff);
scene.add(ambientLight);
const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
directionalLight.position.set(5, 10, 5);
scene.add(directionalLight);

const response = await fetch('http://127.0.0.1:8001/data');
const data = await response.json();
const containerDims = data['dimensions'];
const boxesData = data['boxes_data'];

// Main container box
const containerDimensions = { width: containerDims[0], height: containerDims[1], depth: containerDims[2] };
const containerGeometry = new THREE.BoxGeometry(
    containerDimensions.width,
    containerDimensions.depth, // Swapped depth and height for vertical orientation
    containerDimensions.height
);

// Create container outline
const containerEdges = new THREE.EdgesGeometry(containerGeometry);
const containerLine = new THREE.LineSegments(
    containerEdges,
    new THREE.LineBasicMaterial({ color: 0x000000, linewidth: 2 })
);
scene.add(containerLine);


const boxes = [];
let currentBoxIndex = 0;

// Create boxes with different colors
function createBox(data) {
    const geometry = new THREE.BoxGeometry(...data.size);
    const material = new THREE.MeshPhongMaterial({
        color: new THREE.Color(Math.random() * 0.5 + 0.5, Math.random() * 0.5 + 0.5, Math.random() * 0.5 + 0.5),
        transparent: true,
        opacity: 0.9
    });
    const box = new THREE.Mesh(geometry, material);
    
    // Position at the entry point
    box.position.set(
        -containerDimensions.width / 2 + data.pos[0] + data.size[0] / 2,
        containerDimensions.depth / 2 + data.pos[1] + data.size[1] / 2,
        -containerDimensions.height / 2 + data.pos[2] + data.size[2] / 2,
    );
    
    return box;
}

// Animation variables
let animating = false;
let currentBox = null;
const animationSpeed = containerDimensions.depth / 10;

function startAnimation() {
    if (currentBoxIndex >= boxesData.length || animating) return;
    
    currentBox = createBox(boxesData[currentBoxIndex]);
    scene.add(currentBox);
    boxes.push(currentBox);
    animating = true;
}
function stepBackward() {
    if (boxes.length > 0) {
        const lastBox = boxes.pop();
        scene.remove(lastBox);

        currentBoxIndex = Math.max(0, currentBoxIndex - 1);
        animating = false;
    }
}

function resetAnimation() {
    boxes.forEach(box => scene.remove(box));
    boxes.length = 0;
    currentBoxIndex = 0;
    animating = false;
    currentBox = null;
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);

    if (animating && currentBox) {
        // Calculate target Y position (vertical drop)
        const targetY = -containerDimensions.depth/2 + boxesData[currentBoxIndex].pos[1] + boxesData[currentBoxIndex].size[1]/2;
        
        // Check for collision with other boxes
        let collisionHeight = targetY;
        boxes.forEach(box => {
            if (box !== currentBox) {
                // Simple collision detection
                const xDiff = Math.abs(box.position.x - currentBox.position.x);
                const zDiff = Math.abs(box.position.z - currentBox.position.z);
                if (xDiff < (box.geometry.parameters.width + currentBox.geometry.parameters.width) / 2 &&
                    zDiff < (box.geometry.parameters.depth + currentBox.geometry.parameters.depth) / 2) {
                    collisionHeight = Math.max(collisionHeight, 
                        box.position.y + box.geometry.parameters.height/2 + currentBox.geometry.parameters.height/2);
                }
            }
        });

        if (currentBox.position.y > collisionHeight) {
            currentBox.position.y -= animationSpeed;
        } else {
            currentBox.position.y = collisionHeight;
            animating = false;
            currentBoxIndex++;
        }
    }

    controls.update();
    renderer.render(scene, camera);
}

// Camera position for top-down view with slight angle
camera.position.set(containerDimensions.width, containerDimensions.depth, containerDimensions.height);
camera.lookAt(0, 0, 0);

// Create OrbitControls for mouse interaction
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; // Enable smooth damping for the controls
controls.dampingFactor = 0.25; // Adjust damping speed
controls.screenSpacePanning = false; // Disable panning vertically

// Event listeners
document.getElementById('startAnimation').addEventListener('click', startAnimation);
document.getElementById('resetAnimation').addEventListener('click', resetAnimation);
document.getElementById('stepBackward').addEventListener('click', stepBackward);

// Handle window resize
window.addEventListener('resize', onWindowResize, false);
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

animate();
// Blockchain Animation and Tooltip Control
document.addEventListener('DOMContentLoaded', function() {
    // Animation für die Blockchain-Knoten und Verbindungslinien
    const nodes = document.querySelectorAll('.node');
    const connectingDots = document.querySelectorAll('.connecting-dot');
    
    // Animate nodes with delay
    nodes.forEach((node, index) => {
        setTimeout(() => {
            node.classList.add('active');
        }, index * 300);
    });
    
    // Animate connecting dots with delay
    connectingDots.forEach((dot, index) => {
        setTimeout(() => {
            dot.classList.add('pulse');
        }, index * 200 + 500);
    });
    
    // Tooltips sind jetzt permanent sichtbar und benötigen keine Hover-Logik mehr
    // Jeder Knoten hat weiterhin das data-info Attribut zur besseren Nachvollziehbarkeit
    console.log('Permanent tooltips layout activated');
});

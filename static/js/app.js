/**
 * Global UI: mobile sidebar toggle
 */
(function () {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const toggle = document.getElementById("sidebarToggle");

    if (!sidebar || !overlay) return;

    function openSidebar() {
        sidebar.classList.add("open");
        overlay.classList.add("show");
    }

    function closeSidebar() {
        sidebar.classList.remove("open");
        overlay.classList.remove("show");
    }

    toggle?.addEventListener("click", openSidebar);
    overlay.addEventListener("click", closeSidebar);
})();

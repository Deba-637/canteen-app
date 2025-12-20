// --- Global ---
let currentOperatorId = null;
let currentOperatorName = null;

document.addEventListener('DOMContentLoaded', () => {
    // Session Restore
    if (sessionStorage.getItem('canteen_role')) {
        currentOperatorId = sessionStorage.getItem('canteen_op_id');
        currentOperatorName = sessionStorage.getItem('canteen_op_user');
    }

    // --- Page Specific Init ---
    const path = window.location.pathname;
    if (path === '/admin') {
        initAdmin();
    } else if (path === '/operator') {
        initOperator();
    } else if (path === '/' || path.endsWith('login.html')) {
        initLogin();
    }
});

function logout() {
    sessionStorage.clear();
    window.location.href = '/';
}

// --- Login Logic ---
function initLogin() {
    if (!document.getElementById('login-username')) return;

    let loginRole = 'operator';
    window.setLoginRole = function (role) {
        loginRole = role;
        document.getElementById('btn-role-operator').classList.toggle('active', role === 'operator');
        document.getElementById('btn-role-admin').classList.toggle('active', role === 'admin');
    }

    window.handleLogin = async function () {
        const user = document.getElementById('login-username').value;
        const pass = document.getElementById('login-password').value;

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: loginRole, username: user, password: pass })
            });

            if (!res.ok) {
                const text = await res.text();
                alert(`Server Error (${res.status}): ${text.substring(0, 200)}`);
                return;
            }

            const data = await res.json();

            if (data.status === 'success') {
                sessionStorage.setItem('canteen_role', data.role);
                if (data.role === 'operator') {
                    sessionStorage.setItem('canteen_op_id', data.id);
                    sessionStorage.setItem('canteen_op_user', data.username);
                    window.location.href = '/operator';
                } else {
                    window.location.href = '/admin';
                }
            } else {
                alert(data.message);
            }
        } catch (e) {
            console.error(e);
            alert("Client/Network Error: " + e.message);
        }
    }
}

// --- Admin Logic (Global) ---

window.showTab = function (tabId) {
    // Toggle Sections
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active-section'));
    const activeEl = document.getElementById(tabId);
    if (activeEl) activeEl.classList.add('active-section');

    // Toggle Tabs
    document.querySelectorAll('.tabs button').forEach(el => el.classList.remove('active'));
    // Try to find the button that called this
    const btn = document.querySelector(`button[onclick="showTab('${tabId}')"]`);
    if (btn) btn.classList.add('active');

    // Load Data
    if (tabId === 'admin-students') loadStudents();
    if (tabId === 'admin-operators') loadOperators();
    if (tabId === 'admin-reports') loadReports();
}

window.addStudent = async function () {
    const id = document.getElementById('edit-std-id').value;
    const name = document.getElementById('new-std-name').value;
    const roll = document.getElementById('new-std-roll').value;
    const phone = document.getElementById('new-std-phone').value;
    // const status = document.getElementById('new-std-status').value; // Deprecated
    const remaining = document.getElementById('new-std-remaining').value || 0;
    const mode = document.getElementById('new-std-mode').value;
    const branch = document.getElementById('new-std-branch').value || 'General';
    const amount = document.getElementById('new-std-amount').value || 0;

    if (!name) return alert("Enter Student Name");

    try {
        const method = id ? 'PUT' : 'POST';
        const body = {
            name: name,
            roll: roll,
            phone: phone,

            // payment_status: status,
            remaining_amount: remaining,
            payment_mode: mode,
            dept: branch,
            amount_paid: amount
        };
        if (id) body.id = id;

        const res = await fetch('/api/students', {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (!res.ok) {
            const errData = await res.json();
            alert("Error: " + (errData.error || errData.message || "Unknown error"));
            return;
        }

        // Reset form
        document.getElementById('edit-std-id').value = '';
        document.getElementById('new-std-name').value = '';
        document.getElementById('new-std-roll').value = '';
        document.getElementById('new-std-phone').value = '';
        document.getElementById('new-std-branch').value = '';
        document.getElementById('new-std-amount').value = '';
        document.getElementById('btn-add-student').textContent = 'Add Student';
        document.getElementById('btn-add-student').classList.remove('warning-btn'); // if we use different color for update

        loadStudents();
    } catch (e) { alert("Error saving student: " + e); }
}

window.editStudent = function (student) {
    // Populate Modal
    document.getElementById('edit-modal-id').value = student.id;
    document.getElementById('edit-modal-name').value = student.name;
    document.getElementById('edit-modal-roll').value = student.roll || '';
    document.getElementById('edit-modal-dept').value = student.dept || '';
    document.getElementById('edit-modal-phone').value = student.phone || '';
    document.getElementById('edit-modal-remaining').value = student.remaining_amount || 0;

    // Show Modal
    document.getElementById('edit-modal').classList.remove('hidden');
}

window.submitEditStudent = async function () {
    const id = document.getElementById('edit-modal-id').value;
    const name = document.getElementById('edit-modal-name').value;
    const roll = document.getElementById('edit-modal-roll').value;
    const dept = document.getElementById('edit-modal-dept').value;
    const phone = document.getElementById('edit-modal-phone').value;
    const remaining = document.getElementById('edit-modal-remaining').value;

    if (!name) return alert("Name is required");

    try {
        const res = await fetch('/api/students', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: id,
                name: name,
                roll: roll,
                dept: dept,
                phone: phone,
                remaining_amount: remaining
                // We preserve other fields implicitly in backend or they are not editable here
            })
        });

        if (res.ok) {
            alert("Student Updated Successfully");
            document.getElementById('edit-modal').classList.add('hidden');
            loadStudents();
        } else {
            const err = await res.json();
            alert("Update Failed: " + (err.error || "Unknown Error"));
        }
    } catch (e) {
        alert("Network Error: " + e);
    }
}

window.deleteStudent = async function (id) {
    console.log("Delete Requested for ID:", id);
    if (confirm("Confirm: Delete student ID " + id + "?")) {
        try {
            const res = await fetch(`/api/students?id=${id}`, { method: 'DELETE' });
            if (res.ok) {
                // Check if we were editing this one
                if (document.getElementById('edit-std-id').value == id) {
                    // Reset form
                    document.getElementById('edit-std-id').value = '';
                    document.getElementById('btn-add-student').textContent = 'Add Student';
                }
                alert("Success: Student deleted.");
                loadStudents();
            } else {
                const err = await res.text();
                alert("Failed: Server returned " + res.status + "\n" + err);
            }
        } catch (e) {
            console.error(e);
            alert("Network Error during delete: " + e);
        }
    }
}

window.addOperator = async function () {
    const user = document.getElementById('new-op-user').value;
    const pass = document.getElementById('new-op-pass').value;
    if (!user || !pass) return alert("Fill details");

    try {
        await fetch('/api/operators', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        document.getElementById('new-op-user').value = '';
        document.getElementById('new-op-pass').value = '';
        loadOperators();
    } catch (e) { alert("Error adding operator: " + e); }
}

window.deleteOperator = async function (id) {
    if (confirm("Delete Operator ID " + id + "?")) {
        try {
            const res = await fetch(`/api/operators?id=${id}`, { method: 'DELETE' });
            if (res.ok) {
                alert("Operator Deleted");
                loadOperators();
            } else {
                alert("Delete Failed");
            }
        } catch (e) { alert("Error deleting operator: " + e); }
    }
}

window.exportCSV = function () {
    window.location.href = '/api/export';
}

window.updateExcel = async function () {
    try {
        const btn = document.querySelector('button[onclick="updateExcel()"]');
        const originalText = btn.textContent;
        btn.textContent = "Updating...";
        btn.disabled = true;

        const res = await fetch('/api/backup/excel', { method: 'POST' });
        const data = await res.json();

        if (data.status === 'success') {
            alert("Success: " + data.message);
        } else {
            alert("Error: " + data.message);
        }
        btn.textContent = originalText;
        btn.disabled = false;
    } catch (e) {
        alert("Network Error: " + e);
    }
}

async function loadStudents() {
    try {
        const res = await fetch('/api/students', { cache: 'no-store' });
        const data = await res.json();
        const tbody = document.getElementById('admin-students-list');
        if (tbody) {
            tbody.innerHTML = '';
            data.forEach((s, index) => {
                // Serialize object for edit function
                const sData = JSON.stringify(s).replace(/"/g, "&quot;");
                tbody.innerHTML += `
                    <tr>
                        <td>${index + 1} (ID: ${s.id})</td>
                        <td>${s.name}</td>
                        <td>${s.roll || '-'}</td>
                        <td>${s.phone || '-'}</td>
                        <td>${s.dept || '-'}</td>
                        <td>B:${s.breakfast_count} / L:${s.lunch_count} / D:${s.dinner_count}</td>
                        <td style="color: ${s.remaining_amount > 0 ? 'red' : 'green'}; font-weight: bold;">₹${s.remaining_amount || 0}</td>
                        <td>₹${s.amount_paid || 0}</td>
                        <td>
                            <button onclick="window.editStudent(${sData})" class="primary-btn" style="padding: 5px 10px; font-size: 0.8em;">Edit</button>
                            <button onclick="window.openPayModal(${s.id}, '${s.name}')" class="primary-btn" style="padding: 5px 10px; font-size: 0.8em; background-color: #27ae60; margin-left: 5px;">Pay</button>
                            <button onclick="window.viewStudentReport(${s.id})" class="secondary-btn" style="padding: 5px 10px; font-size: 0.8em; margin-left: 5px;">Report</button>
                            <button onclick="window.deleteStudent(${s.id})" class="danger-btn" style="padding: 5px 10px; font-size: 0.8em; margin-left: 5px;">Delete</button>
                        </td>
                    </tr>
                `;
            });
        }
    } catch (e) { console.error("Load Students Fault", e); }
}

async function loadOperators() {
    try {
        const res = await fetch('/api/operators', { cache: 'no-store' });
        const data = await res.json();
        const tbody = document.getElementById('admin-operators-list');
        if (tbody) {
            tbody.innerHTML = '';
            data.forEach(op => {
                tbody.innerHTML += `
                    <tr>
                        <td>${op.id}</td>
                        <td>${op.username}</td>
                        <td><button onclick="window.deleteOperator(${op.id})" class="danger-btn">Delete</button></td>
                    </tr>
                `;
            });
        }
    } catch (e) { console.error("Load Operators Fault", e); }
}

async function loadReports() {
    try {
        const res = await fetch('/api/reports/meals');
        const stats = await res.json();
        const div = document.getElementById('admin-meal-stats');
        if (div) {
            let html = '<ul>';
            for (const [meal, count] of Object.entries(stats)) {
                if (meal === 'revenue') continue;
                html += `<li><strong>${meal}:</strong> ${count}</li>`;
            }
            html += '</ul>';
            if (stats.revenue !== undefined) {
                html += `<div style="margin-top: 10px; border-top: 1px solid #ddd; padding-top: 5px;">
                            <strong>Total Collection:</strong> <span style="color: green; font-weight: bold; font-size: 1.1em;">₹${stats.revenue}</span>
                         </div>`;
            }
            div.innerHTML = html;
        }
    } catch (e) { console.error("Load Reports Fault", e); }
}

window.viewStudentReport = async function (id) {
    try {
        const res = await fetch(`/api/reports/student/${id}`);
        if (!res.ok) {
            const err = await res.json();
            alert("Error: " + (err.error || "Failed to load report"));
            return;
        }

        const data = await res.json();
        const std = data.student;

        // Populate Meta
        document.getElementById('report-meta').innerHTML = `
            <p><strong>Name:</strong> ${std.name} (${std.roll || 'N/A'})</p>
            <p><strong>Remaining (Debt):</strong> <span style="color:red">₹${std.remaining_amount || 0}</span></p>
            <p><strong>Total Paid:</strong> ₹${std.amount_paid || 0}</p>
        `;

        // Populate Meals
        const mealTbody = document.getElementById('report-meals-list');
        mealTbody.innerHTML = '';
        if (data.meals.length === 0) {
            mealTbody.innerHTML = '<tr><td colspan="4">No meals recorded.</td></tr>';
        } else {
            data.meals.forEach(m => {
                mealTbody.innerHTML += `
                    <tr>
                        <td>${m.date}</td>
                        <td>${m.breakfast ? 'Yes' : '-'}</td>
                        <td>${m.lunch ? 'Yes' : '-'}</td>
                        <td>${m.dinner ? 'Yes' : '-'}</td>
                    </tr>
                `;
            });
        }

        // Populate Money
        const moneyTbody = document.getElementById('report-money-list');
        moneyTbody.innerHTML = '';
        if (data.transactions.length === 0) {
            moneyTbody.innerHTML = '<tr><td colspan="5">No transactions found.</td></tr>';
        } else {
            // Header needs update to support mixed types? 
            // Current header: Date | Bill No | Item | Amount | Mode
            // For Payment: Date | - | Fee Payment | Amount | Mode
            data.transactions.forEach(t => {
                const isPay = t.type === 'Payment';
                moneyTbody.innerHTML += `
                    <tr style="background-color: ${isPay ? '#e8f8f5' : 'inherit'}">
                        <td>${t.date}</td>
                        <td>${t.type === 'Food' ? '#' : ''}</td>
                        <td>${t.item}</td>
                        <td style="color: ${t.color}; font-weight: bold;">₹${t.amount}</td>
                        <td>${t.mode}</td>
                    </tr>
                `;
            });
        }

        // Show Modal
        document.getElementById('report-modal').classList.remove('hidden');

    } catch (e) {
        console.error(e);
        alert("Network Error loading report");
    }
}

window.openPayModal = function (id, name) {
    document.getElementById('pay-student-id').value = id;
    document.getElementById('pay-student-name').textContent = "Paying for: " + name;
    document.getElementById('pay-amount').value = '';
    document.getElementById('pay-modal').classList.remove('hidden');
    document.getElementById('pay-amount').focus();
}

window.submitPayment = async function () {
    const id = document.getElementById('pay-student-id').value;
    const amount = document.getElementById('pay-amount').value;
    const mode = document.getElementById('pay-mode').value;

    if (!amount || amount <= 0) return alert("Enter valid amount");

    try {
        const res = await fetch('/api/students/pay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: id, amount: amount, mode: mode })
        });

        const data = await res.json();
        if (data.status === 'success') {
            alert("Payment Successful!");
            document.getElementById('pay-modal').classList.add('hidden');
            loadStudents(); // Refresh table
        } else {
            alert("Error: " + data.error);
        }
    } catch (e) {
        alert("Network Error: " + e);
    }
}

function initAdmin() {
    // Guard
    if (sessionStorage.getItem('canteen_role') !== 'admin') {
        window.location.href = '/';
        return;
    }
    // Load initial
    showTab('admin-students');

    // Search Listener
    const searchInput = document.getElementById('admin-student-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#admin-students-list tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }

    // Enter Key Listener for Add Student
    const inputs = document.querySelectorAll('#new-std-name, #new-std-roll, #new-std-branch, #new-std-amount, #new-std-remaining, #new-std-mode');
    console.log("Attached Enter Listener to " + inputs.length + " inputs");

    inputs.forEach(input => {
        input.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                console.log("Enter pressed in " + input.id);
                addStudent();
            }
        });
    });
}


// --- Operator Logic ---
function initOperator() {
    if (sessionStorage.getItem('canteen_role') !== 'operator') {
        window.location.href = '/';
        return;
    }

    const opName = sessionStorage.getItem('canteen_op_user');
    if (opName && document.getElementById('op-username-display')) {
        document.getElementById('op-username-display').textContent = opName;
    }

    loadOperatorData();

    // Event Listeners for search
    const searchInput = document.getElementById('bill-student-search');
    if (searchInput) {
        searchInput.addEventListener('change', handleStudentSearch);
        searchInput.addEventListener('input', handleStudentSearch);
    }
}
// (Functions for operator like generateBill kept global or attached to window if needed, or defined here)
// Currently initOperator logic was defining them on window. Let's make them global to be safe.

window.toggleUserType = function () {
    const type = document.querySelector('input[name="userType"]:checked').value;
    if (type === 'hostel') {
        const h = document.getElementById('input-hostel'); if (h) h.classList.remove('hidden');
        const s = document.getElementById('input-staff'); if (s) s.classList.add('hidden');
        const n = document.getElementById('input-normal'); if (n) n.classList.add('hidden');
    } else if (type === 'staff') {
        const h = document.getElementById('input-hostel'); if (h) h.classList.add('hidden');
        const s = document.getElementById('input-staff'); if (s) s.classList.remove('hidden');
        const n = document.getElementById('input-normal'); if (n) n.classList.add('hidden');
    } else {
        const h = document.getElementById('input-hostel'); if (h) h.classList.add('hidden');
        const s = document.getElementById('input-staff'); if (s) s.classList.add('hidden');
        const n = document.getElementById('input-normal'); if (n) n.classList.remove('hidden');
    }
}

window.generateBill = async function () {
    const userType = document.querySelector('input[name="userType"]:checked').value;
    const meal = document.getElementById('bill-meal-type').value;
    const amount = document.getElementById('bill-amount').value;
    const mode = document.getElementById('bill-payment-mode').value;

    let studentId = null;
    let guestName = null;

    if (userType === 'hostel') {
        studentId = document.getElementById('bill-student-id').value;
        if (!studentId) {
            const val = document.getElementById('bill-student-search').value;
            const match = val.match(/\[ID: (\d+)\]/);
            if (match) studentId = match[1];
        }
        if (!studentId) return alert("Select a valid student.");
    } else if (userType === 'staff') {
        guestName = document.getElementById('bill-staff-name').value;
        if (!guestName) return alert("Enter Staff Name.");
    } else {
        guestName = document.getElementById('bill-guest-name').value || "Guest";
    }

    try {
        const res = await fetch('/api/bill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_type: userType,
                student_id: studentId,
                guest_name: guestName,
                meal_type: meal,
                amount: amount,
                payment_mode: mode,
                operator_id: currentOperatorId
            })
        });
        const data = await res.json();
        if (data.status === 'success') {
            const width = 400; const height = 600;
            const left = (screen.width - width) / 2;
            const top = (screen.height - height) / 2;
            window.open(`/bill-view/${data.bill_no}`, 'BillPrint', `width=${width},height=${height},top=${top},left=${left}`);

            // Clear inputs
            if (userType === 'normal') document.getElementById('bill-guest-name').value = '';
            if (userType === 'staff') document.getElementById('bill-staff-name').value = '';
            if (userType === 'hostel') {
                document.getElementById('bill-student-search').value = '';
                document.getElementById('bill-student-id').value = '';
            }
            loadLiveStats();
        } else {
            alert("Error: " + data.message);
        }
    } catch (e) { console.error(e); alert("Network Error"); }
}

async function loadOperatorData() {
    try {
        const res = await fetch('/api/students');
        const data = await res.json();
        const datalist = document.getElementById('student-list');
        if (datalist) {
            datalist.innerHTML = '';
            data.forEach(s => {
                const opt = document.createElement('option');
                // Improved format: Name (Roll: X) [ID: Y]
                const rollStr = s.roll ? `Roll: ${s.roll}` : 'No Roll';
                opt.value = `${s.name} (${rollStr}) [ID: ${s.id}]`;
                datalist.appendChild(opt);
            });
        }
        loadLiveStats();
    } catch (e) { console.error("Op Data Error", e); }
}

function handleStudentSearch(e) {
    const val = e.target.value;
    // Match [ID: 123]
    const match = val.match(/\[ID: (\d+)\]/);
    if (match) {
        document.getElementById('bill-student-id').value = match[1];
    } else {
        document.getElementById('bill-student-id').value = '';
    }
}

async function loadLiveStats() {
    try {
        const res = await fetch('/api/reports/meals');
        const stats = await res.json();
        const div = document.getElementById('op-meal-stats');
        if (div) {
            let html = '';
            for (const [meal, count] of Object.entries(stats)) {
                if (meal === 'revenue') continue;
                html += `<div>${meal}: ${count}</div>`;
            }
            if (stats.revenue !== undefined) {
                html += `<div style="margin-top: 10px; border-top: 1px solid #ccc; padding-top: 5px; font-weight: bold;">
                            Total: <span style="color: #2ecc71;">₹${stats.revenue}</span>
                          </div>`;
            }
            div.innerHTML = html || 'No meals served.';
        }
    } catch (e) { console.error("Stats Error", e); }
}

window.selectOption = function (inputId, value, btnElement) {
    // defined global to be accessible from onclick
    document.getElementById(inputId).value = value;

    // Toggle active class on buttons in the same group
    const group = btnElement.parentElement;
    const buttons = group.querySelectorAll('.option-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    btnElement.classList.add('active');
}

window.selectAmount = function (value, btnElement) {
    const input = document.getElementById('bill-amount');

    // Toggle active class
    const group = btnElement.parentElement;
    const buttons = group.querySelectorAll('.option-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    btnElement.classList.add('active');

    if (value === 'other') {
        input.focus();
        // If user types, we keep "Other" selected visually
    } else {
        input.value = value;
    }
}

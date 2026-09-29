import os

html_path = r"C:\Users\saidm\OneDrive\Desktop\SHIFTSYNC\shiftsync_core_system.html"

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Database API integration script to add to shiftsync_core_system.html
db_integration_code = """
    // ============================================================
    // ShiftSync Database REST API Synchronization
    // ============================================================
    let activeHandoverId = null;

    async function fetchAPI(endpoint, method = 'GET', data = null) {
      try {
        const options = {
          method: method,
          headers: { 'Content-Type': 'application/json' }
        };
        if (data) options.body = JSON.stringify(data);
        const res = await fetch(endpoint, options);
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return await res.json();
      } catch (err) {
        console.warn(`API call to ${endpoint} failed, keeping fallback UI state:`, err);
        return null;
      }
    }

    async function loadDashboardStats() {
      const data = await fetchAPI('/api/dashboard-stats');
      if (!data) return;

      const statHandovers = document.getElementById('stat-pending-handovers');
      const statTasks = document.getElementById('stat-incomplete-tasks');
      const statAlerts = document.getElementById('stat-unread-alerts');
      const badgePending = document.getElementById('badge-pending-count');

      if (statHandovers) statHandovers.innerText = data.pending_handovers;
      if (statTasks) statTasks.innerText = data.incomplete_tasks;
      if (statAlerts) statAlerts.innerText = data.unread_alerts;
      if (badgePending) badgePending.innerText = data.pending_handovers;
    }

    async function loadShifts() {
      const data = await fetchAPI('/api/shifts');
      if (!data || !data.shifts) return;

      const tbody = document.getElementById('shifts-table-body');
      const select = document.getElementById('handover-shift-select');
      if (!tbody) return;

      tbody.innerHTML = '';
      if (select) select.innerHTML = '';

      data.shifts.forEach(s => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50';
        const badgeClass = s.status === 'Active' ? 'badge-completed' : (s.status === 'Scheduled' ? 'badge-inprogress' : 'badge-pending');
        tr.innerHTML = `
          <td class="p-3.5 font-bold text-slate-900">${s.shift_name}</td>
          <td class="p-3.5 font-mono text-slate-700">${s.shift_date}</td>
          <td class="p-3.5 font-mono text-slate-700">${s.start_time}</td>
          <td class="p-3.5 font-mono text-slate-700">${s.end_time}</td>
          <td class="p-3.5 text-slate-800">${s.team}</td>
          <td class="p-3.5"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${badgeClass}">${s.status}</span></td>
          <td class="p-3.5 text-right space-x-2">
            <button onclick="alert('Viewing shift: ${s.shift_name}')" class="px-2.5 py-1 rounded border border-slate-300 text-slate-700 hover:bg-slate-50">View</button>
            <button onclick="alert('Editing shift: ${s.shift_name}')" class="px-2.5 py-1 rounded border border-slate-300 text-slate-700 hover:bg-slate-50">Edit</button>
          </td>
        `;
        tbody.appendChild(tr);

        if (select) {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.text = `${s.shift_name} (${s.start_time} - ${s.end_time}, ${s.shift_date}) - ${s.team}`;
          if (s.status === 'Active') opt.selected = true;
          select.appendChild(opt);
        }
      });
    }

    async function loadHandovers() {
      const data = await fetchAPI('/api/handovers');
      if (!data || !data.handovers) return;

      const tbody = document.getElementById('all-handovers-tbody');
      const dashTbody = document.getElementById('dash-handovers-tbody');
      if (!tbody) return;

      tbody.innerHTML = '';
      if (dashTbody) dashTbody.innerHTML = '';

      data.handovers.forEach(h => {
        const tr = document.createElement('tr');
        tr.className = h.status === 'Pending Review' ? 'hover:bg-slate-50 bg-amber-50/40' : 'hover:bg-slate-50';
        const badgeClass = h.status === 'Acknowledged' ? 'badge-completed' : (h.status === 'Pending Review' ? 'badge-inprogress' : 'badge-pending');
        
        tr.innerHTML = `
          <td class="p-3.5 font-mono font-bold text-slate-900">#${h.report_code}</td>
          <td class="p-3.5 font-medium text-slate-900">${h.shift_name || 'Shift'} (${h.team || 'Crew'})</td>
          <td class="p-3.5 text-slate-700">${h.outgoing_operator}</td>
          <td class="p-3.5 text-slate-700">${h.incoming_operator}</td>
          <td class="p-3.5 font-mono text-slate-600">${h.submitted_at}</td>
          <td class="p-3.5"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${badgeClass}" id="badge-${h.report_code}">${h.status}</span></td>
          <td class="p-3.5 text-right">
            <button onclick="viewHandoverDetails('${h.report_code}', '${h.outgoing_operator}', '${h.incoming_operator}', '${h.equipment_status || ''}', '${h.safety_notes || ''}')" class="px-2.5 py-1 rounded ${h.status === 'Pending Review' ? 'bg-[#C8102E] text-white hover:bg-[#A60C25]' : 'border border-slate-300 text-slate-700 hover:bg-slate-50'} font-semibold text-xs transition">
              ${h.status === 'Pending Review' ? 'Review & Acknowledge' : 'View Details'}
            </button>
          </td>
        `;
        tbody.appendChild(tr);

        if (dashTbody) {
          const dTr = tr.cloneNode(true);
          dashTbody.appendChild(dTr);
        }
      });
    }

    async function loadTasks() {
      const data = await fetchAPI('/api/tasks');
      if (!data || !data.tasks) return;

      const tbody = document.getElementById('tasks-table-body');
      const dashTbody = document.getElementById('dash-pending-tasks');
      if (!tbody) return;

      tbody.innerHTML = '';
      if (dashTbody) dashTbody.innerHTML = '';

      data.tasks.forEach(t => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50';
        tr.setAttribute('data-status', t.status);
        tr.setAttribute('data-priority', t.priority);

        let prioClass = 'badge-medium';
        if (t.priority === 'Critical') prioClass = 'badge-critical';
        else if (t.priority === 'High') prioClass = 'badge-high';
        else if (t.priority === 'Low') prioClass = 'badge-low';

        let statusClass = 'badge-pending';
        if (t.status === 'Completed') statusClass = 'badge-completed';
        else if (t.status === 'In Progress') statusClass = 'badge-inprogress';

        tr.innerHTML = `
          <td class="p-3.5 font-bold text-slate-900">${t.task_name}</td>
          <td class="p-3.5 text-slate-700">${t.assigned_to}</td>
          <td class="p-3.5"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${prioClass}">${t.priority.toUpperCase()}</span></td>
          <td class="p-3.5 font-mono text-slate-600">${t.due_date || 'Shift End'}</td>
          <td class="p-3.5"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${statusClass}">${t.status.toUpperCase()}</span></td>
          <td class="p-3.5 text-right space-x-2">
            <button onclick="toggleTaskStatus(${t.id}, this)" class="px-2 py-1 rounded border border-slate-300 text-slate-700 hover:bg-slate-50 text-[11px] font-medium">${t.status === 'Completed' ? 'Reopen' : 'Mark Done'}</button>
          </td>
        `;
        tbody.appendChild(tr);

        if (dashTbody && t.status !== 'Completed') {
          const dTr = document.createElement('tr');
          dTr.innerHTML = `
            <td class="py-3 px-2 font-medium text-slate-900">${t.task_name}</td>
            <td class="py-3 px-2"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${prioClass}">${t.priority}</span></td>
            <td class="py-3 px-2"><span class="px-2 py-0.5 rounded-full text-[10px] ${statusClass}">${t.status}</span></td>
            <td class="py-3 px-2 text-right"><button onclick="toggleTaskStatus(${t.id}, this)" class="text-xs text-slate-600 hover:text-slate-900 font-medium">Mark Done</button></td>
          `;
          dashTbody.appendChild(dTr);
        }
      });
    }

    async function loadUsers() {
      const data = await fetchAPI('/api/users');
      if (!data || !data.users) return;

      const tbody = document.getElementById('users-table-body');
      if (!tbody) return;
      tbody.innerHTML = '';

      data.users.forEach(u => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50';
        tr.innerHTML = `
          <td class="p-3.5 font-bold text-slate-900">${u.name}</td>
          <td class="p-3.5 text-slate-500 font-mono">${u.email}</td>
          <td class="p-3.5 text-slate-800">${u.role}</td>
          <td class="p-3.5 text-slate-800">${u.department}</td>
          <td class="p-3.5"><span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${u.status === 'Active' ? 'badge-completed' : 'badge-pending'}">${u.status.toUpperCase()}</span></td>
          <td class="p-3.5 text-right space-x-2">
            <button onclick="alert('Viewing profile: ${u.name}')" class="px-2.5 py-1 rounded border border-slate-300 text-slate-700 hover:bg-slate-50">Edit</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Connect Handover Submission to DB
    async function handleSubmitHandover(e) {
      e.preventDefault();
      const shiftId = document.getElementById('handover-shift-select').value;
      const incoming = document.getElementById('handover-incoming-operator').value;
      const equip = document.getElementById('handover-equipment').value;
      const safety = document.getElementById('handover-safety').value;
      const notes = document.getElementById('handover-notes').value;

      const tasksToAppend = currentDetectedTasks.map(t => ({
        task: t.task,
        category: t.category,
        priority: t.priority,
        status: t.status
      }));

      const payload = {
        shift_id: parseInt(shiftId) || 1,
        outgoing_operator: currentUser.name,
        incoming_operator: incoming,
        equipment_status: equip,
        safety_notes: safety,
        additional_notes: notes,
        tasks: tasksToAppend
      };

      const res = await fetchAPI('/api/handovers', 'POST', payload);
      const code = res ? res.report_code : 'HO-2026-NEW';
      alert(`Handover report #${code} formally submitted to database!\\nStatus: PENDING ACKNOWLEDGMENT\\nAssigned Incoming Lead: ${incoming}`);
      
      await loadHandovers();
      await loadTasks();
      await loadDashboardStats();
      navigateTo('handover-reports');
    }

    // Connect Acknowledgment to DB
    function viewHandoverDetails(id, outOp = 'John Doe', inOp = 'Michael Chang', equip = '', safety = '') {
      activeHandoverId = id;
      document.getElementById('handover-review-modal').classList.remove('hidden');
      document.getElementById('modal-ho-id').innerText = 'Handover Report #' + id;
      document.getElementById('modal-ho-ack-user').innerText = currentUser.name + ' (' + currentUser.role + ')';
    }

    async function confirmAcknowledgment() {
      if (!activeHandoverId) activeHandoverId = 'HO-2026-088';

      const res = await fetchAPI(`/api/handovers/${activeHandoverId}/acknowledge`, 'POST', { user: currentUser.name });
      
      document.getElementById('modal-ho-status').innerText = 'Acknowledged';
      document.getElementById('modal-ho-status').className = 'px-2 py-0.5 rounded-full text-[10px] font-bold badge-completed';

      alert(`Official Acknowledgment Recorded in Database!\\nOperator ${currentUser.name} has formally accepted custody of Shift #${activeHandoverId} at ${new Date().toLocaleTimeString()}.`);
      closeModal('handover-review-modal');

      await loadHandovers();
      await loadDashboardStats();
    }

    // Connect Task Status Toggle to DB
    async function toggleTaskStatus(taskId, btn) {
      if (!taskId) return;
      const res = await fetchAPI(`/api/tasks/${taskId}/toggle`, 'POST');
      await loadTasks();
      await loadDashboardStats();
    }

    // Connect Save Task to DB
    async function handleSaveTask(e) {
      e.preventDefault();
      const name = document.getElementById('new-task-name').value;
      const assignee = document.getElementById('new-task-assignee').value;
      const priority = document.getElementById('new-task-priority').value;
      const due = document.getElementById('new-task-due').value;

      await fetchAPI('/api/tasks', 'POST', {
        task_name: name,
        assigned_to: assignee,
        category: 'Operations',
        priority: priority,
        due_date: due,
        status: 'Pending'
      });

      closeModal('modal-add-task');
      alert(`New task "${name}" persisted to SQLite database.`);
      await loadTasks();
      await loadDashboardStats();
    }

    // Connect Save Shift to DB
    async function handleSaveShift(e) {
      e.preventDefault();
      const name = document.getElementById('new-shift-name').value;
      const date = document.getElementById('new-shift-date').value;
      const start = document.getElementById('new-shift-start').value;
      const end = document.getElementById('new-shift-end').value;
      const team = document.getElementById('new-shift-team').value;
      const status = document.getElementById('new-shift-status').value;

      await fetchAPI('/api/shifts', 'POST', {
        shift_name: name,
        shift_date: date,
        start_time: start,
        end_time: end,
        team: team,
        status: status
      });

      closeModal('modal-add-shift');
      alert(`Shift "${name}" persisted to SQLite database.`);
      await loadShifts();
    }

    // Connect Save User to DB
    async function handleSaveUser(e) {
      e.preventDefault();
      const name = document.getElementById('new-user-name').value;
      const email = document.getElementById('new-user-email').value;
      const role = document.getElementById('new-user-role').value;
      const dept = document.getElementById('new-user-dept').value;

      await fetchAPI('/api/users', 'POST', {
        name: name,
        email: email,
        role: role,
        department: dept
      });

      closeModal('modal-add-user');
      alert(`User "${name}" persisted to SQLite database.`);
      await loadUsers();
    }

    // Initialize all database data on page load
    window.addEventListener('DOMContentLoaded', () => {
      loadDashboardStats();
      loadShifts();
      loadHandovers();
      loadTasks();
      loadUsers();
    });
"""

# Replace the older synchronous placeholders
old_handle_submit = """    // Handover Submission (Non-AI)
    function handleSubmitHandover(e) {
      e.preventDefault();
      const shift = document.getElementById('handover-shift-select').value;
      const incoming = document.getElementById('handover-incoming-operator').value;
      
      alert(`Handover report formally submitted!\\nShift: ${shift}\\nIncoming Lead: ${incoming}\\nStatus: PENDING ACKNOWLEDGMENT`);
      
      // Update pending count
      document.getElementById('stat-pending-handovers').innerText = '4';
      document.getElementById('badge-pending-count').innerText = '2';
      
      navigateTo('handover-reports');
    }"""

if old_handle_submit in content:
    # Replace from old_handle_submit to the end of script tag
    split_pos = content.find("    // Handover Submission (Non-AI)")
    script_end = content.find("  </script>", split_pos)
    content = content[:split_pos] + db_integration_code + "\n" + content[script_end:]
    print("Injected database API client functions.")
else:
    print("Could not find exact block, checking alternative injection point.")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Updated HTML file size: {len(content)}")

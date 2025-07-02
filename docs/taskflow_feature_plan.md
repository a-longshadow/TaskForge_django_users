// UNIFIED Build_Payload_GraphQL - Handles Multiple Meetings & Serves All Downstream Nodes
// Removes emojis from emails, accurate data extraction, proper Railway payload

try {
  const tasks = items || [];
  console.log(`📋 Processing ${tasks.length} tasks for HITL review`);
  
  if (tasks.length === 0) {
    throw new Error('No tasks received from Transform node');
  }
  
  // GROUP TASKS BY MEETING
  const meetingGroups = {};
  let totalTasks = 0;
  
  tasks.forEach(task => {
    const meetingId = task.json?.meeting_id || 'unknown';
    const meetingTitle = task.json?.meeting_title || 'Unknown Meeting';
    const meetingOrganizer = task.json?.meeting_organizer || 'Unknown';
    const meetingDate = task.json?.meeting_date || new Date().toISOString();
    
    if (!meetingGroups[meetingId]) {
      meetingGroups[meetingId] = {
        meeting_title: meetingTitle,
        meeting_organizer: meetingOrganizer,
        meeting_date: meetingDate,
        meeting_id: meetingId,
        tasks: []
      };
    }
    
    meetingGroups[meetingId].tasks.push({
      task_item: task.json?.task_item || `Task ${totalTasks + 1}`,
      'assignee(s)_full_names': task.json?.['assignee(s)_full_names'] || 'Unassigned',
      assignee_emails: task.json?.assignee_emails || '',
      priority: task.json?.priority || 'Medium',
      brief_description: task.json?.brief_description || 'No description',
      date_expected: task.json?.date_expected || new Date().toISOString().split('T')[0],
      meeting_title: meetingTitle,
      meeting_organizer: meetingOrganizer,
      meeting_date: meetingDate,
      meeting_id: meetingId
    });
    
    totalTasks++;
  });
  
  const meetings = Object.values(meetingGroups);
  const execId = `exec_${Date.now()}`;
  
  console.log(`🎯 Found ${meetings.length} meetings with ${totalTasks} total tasks`);
  meetings.forEach(meeting => {
    console.log(`   - "${meeting.meeting_title}" by ${meeting.meeting_organizer}: ${meeting.tasks.length} tasks`);
  });
  
  // FLATTEN ALL TASKS FOR MONDAY.COM
  const allMondayTasks = [];
  meetings.forEach(meeting => {
    allMondayTasks.push(...meeting.tasks);
  });
  
  // CREATE APPROVAL URL
  const approvalUrl = `https://web-production-c8f1d.up.railway.app?exec_id=${execId}`;
  
  // GENERATE MEETING SUMMARY FOR NOTIFICATIONS
  let meetingSummary, organizerSummary;
  if (meetings.length === 1) {
    meetingSummary = meetings[0].meeting_title;
    organizerSummary = meetings[0].meeting_organizer;
  } else {
    meetingSummary = `${meetings.length} meetings (${meetings.map(m => m.meeting_title).join(', ')})`;
    organizerSummary = `Multiple organizers`;
  }
  
  // TELEGRAM MESSAGE (with emojis)
  const telegramMessage = `🔥 TaskForge Review Required

📋 Meeting: ${meetingSummary}
👤 Organizer: ${organizerSummary}
📊 Tasks: ${totalTasks} action items
🆔 ID: ${execId}

👆 CLICK TO APPROVE:
${approvalUrl}

⏰ Time-sensitive - Please review promptly`;

  // EMAIL CONTENT (NO EMOJIS, clean formatting)
  const emailSubject = `TaskForge: ${totalTasks} Action Items Need Review`;
  
  let emailMeetingDetails = '';
  if (meetings.length === 1) {
    emailMeetingDetails = `
<h3>Meeting Details</h3>
<table style="font-family: Arial, sans-serif; border-collapse: collapse; width: 100%;">
  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Meeting:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${meetings[0].meeting_title}</td></tr>
  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Organizer:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${meetings[0].meeting_organizer}</td></tr>
  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Tasks:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${totalTasks} action items</td></tr>
  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Execution ID:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${execId}</td></tr>
</table>`;
  } else {
    emailMeetingDetails = `
<h3>Meeting Details</h3>
<p><strong>Multiple Meetings:</strong> ${meetings.length} meetings</p>
<ul>
${meetings.map(meeting => 
  `<li><strong>${meeting.meeting_title}</strong> by ${meeting.meeting_organizer} (${meeting.tasks.length} tasks)</li>`
).join('')}
</ul>
<p><strong>Total Tasks:</strong> ${totalTasks} action items</p>
<p><strong>Execution ID:</strong> ${execId}</p>`;
  }
  
  const emailHtml = `
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
    <h1 style="margin: 0; font-size: 24px;">TaskForge Review Required</h1>
  </div>
  
  ${emailMeetingDetails}
  
  <div style="text-align: center; margin: 30px 0;">
    <a href="${approvalUrl}" style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">REVIEW TASKS</a>
  </div>
  
  <p style="color: #dc3545; text-align: center; font-weight: bold;">Time-sensitive review required</p>
  <p style="color: #666; font-size: 12px; text-align: center;">This link will expire after use for security</p>
</div>`;

  // RAILWAY PAYLOAD (for HTTP Request node) - Fixed to match server.py expectations
  const railwayPayload = {
    execution_id: execId,
    monday_tasks: allMondayTasks,
    meeting_title: meetingSummary,
    meeting_organizer: organizerSummary,
    total_tasks: totalTasks,
    created_at: new Date().toISOString(),
    // Additional fields for Railway compatibility
    meetings: meetings,
    meeting_count: meetings.length,
    approval_url: approvalUrl,
    status: 'pending'
  };

  // MEETING DATA FOR BUILD PAYLOAD NODE
  const meetingData = meetings.length === 1 ? {
    title: meetings[0].meeting_title,
    organizer: meetings[0].meeting_organizer,
    date: meetings[0].meeting_date,
    id: meetings[0].meeting_id,
    summary: `Meeting with ${meetings[0].tasks.length} action items`
  } : {
    title: `${meetings.length} Meetings`,
    organizer: 'Multiple',
    date: new Date().toISOString(),
    id: execId,
    summary: `${meetings.length} meetings with ${totalTasks} total action items`
  };

  console.log(`✅ Generated unified payload:`);
  console.log(`   - Telegram: ${meetingSummary} (${totalTasks} tasks)`);
  console.log(`   - Email: Clean HTML format, no emojis`);
  console.log(`   - Railway: ${Object.keys(railwayPayload).length} fields`);
  console.log(`   - Build Payload: Meeting data prepared`);

  // RETURN UNIFIED OUTPUT FOR ALL 3 DOWNSTREAM NODES
  return [{
    json: {
      // FOR TELEGRAM NODE
      telegram_message: telegramMessage,
      
      // FOR GMAIL NODE (clean, no emojis)
      email_subject: emailSubject,
      email_html: emailHtml,
      
      // FOR HTTP REQUEST NODE (Railway storage)
      railway_payload: railwayPayload,
      
      // FOR BUILD PAYLOAD NODE (True HITL)
      execution_id: execId,
      monday_tasks: allMondayTasks,
      meeting_title: meetingSummary,
      meeting_organizer: organizerSummary,
      meeting_date: meetings[0]?.meeting_date || new Date().toISOString(),
      meeting_id: meetings[0]?.meeting_id || execId,
      total_tasks: totalTasks,
      meeting_count: meetings.length,
      
      approval: {
        execution_id: execId,
        status: 'pending'
      },
      
      meeting_data: meetingData,
      
      // DEBUGGING INFO
      debug_info: {
        meetings_processed: meetings.length,
        total_tasks: totalTasks,
        meeting_breakdown: meetings.map(m => ({
          title: m.meeting_title,
          organizer: m.meeting_organizer,
          task_count: m.tasks.length
        }))
      }
    }
  }];

} catch (error) {
  console.error('❌ Build_Payload_GraphQL Error:', error.message);
  
  // Emergency fallback
  const execId = `error_${Date.now()}`;
  return [{
    json: {
      telegram_message: `🚨 TaskForge Error: ${error.message}`,
      email_subject: 'TaskForge Error',
      email_html: `<h2>TaskForge Error</h2><p>${error.message}</p><p>Please check the workflow configuration.</p>`,
      railway_payload: {
        execution_id: execId,
        error: error.message,
        status: 'error'
      },
      execution_id: execId,
      monday_tasks: [],
      error: error.message
    }
  }];
}
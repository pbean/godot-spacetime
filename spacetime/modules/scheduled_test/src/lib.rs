use spacetimedb::{table, reducer, ReducerContext, Table};

/// Scheduled table: the SpacetimeDB scheduler fires process_job at the time
/// specified by the scheduled_at column. Insert rows here to queue execution.
#[table(name = scheduled_job, scheduled(process_job), public)]
pub struct ScheduledJob {
    #[primary_key]
    #[auto_inc]
    pub scheduled_id: u64,
    pub scheduled_at: spacetimedb::ScheduleAt,
    pub payload: String,
}

/// Regular (non-scheduled) control table.
#[table(name = job_result, public)]
pub struct JobResult {
    #[primary_key]
    #[auto_inc]
    pub id: u32,
    pub result: String,
}

/// Scheduled reducer: invoked by the SpacetimeDB scheduler when a ScheduledJob
/// row's scheduled_at time is reached. Not intended for direct client invocation.
#[reducer]
pub fn process_job(ctx: &ReducerContext, row: ScheduledJob) {
    ctx.db.job_result().insert(JobResult { id: 0, result: row.payload });
}

/// Regular (non-scheduled) control reducer.
#[reducer]
pub fn record_result(ctx: &ReducerContext, result: String) {
    ctx.db.job_result().insert(JobResult { id: 0, result });
}

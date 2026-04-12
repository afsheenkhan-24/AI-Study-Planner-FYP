-- Student table
create table Students (
  student_id bigint primary key,
  name varchar not null,
  email varchar not null unique,
  preferences text,
  study_level varchar,
  created_at timestamptz not null default now()
);

-- Assignment table
create table Assignments (
  assignment_id bigint primary key,
  student_id bigint not null,
  title text not null,
  description text,
  module text,
  deadline date not null,
  created_at timestamptz not null default now(),

  constraint assignment_student_id_fkey
    foreign key (student_id)
    references Student (student_id)
    on delete cascade
);

-- Task table
create table Task (
  task_id bigint primary key,
  title varchar not null,
  description varchar,
  deadline date not null,
  estimated_time bigint not null,
  status varchar not null,
  created_at timestamptz not null default now(),
  student_id bigint not null,
  assignment_id bigint,

  constraint task_student_id_fkey
    foreign key (student_id)
    references Student (student_id)
    on delete cascade,

  constraint task_assignment_id_fkey
    foreign key (assignment_id)
    references Assignment (assignment_id)
    on delete cascade
);

-- StudyPlan table
create table StudyPlan (
  plan_id bigint primary key,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  student_id bigint not null,
  constraint studyplan_student_id_fkey
    foreign key (student_id)
    references Student (student_id)
    on delete cascade
);

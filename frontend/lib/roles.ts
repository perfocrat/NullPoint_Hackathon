export const roles = [
  { value: "backend-developer", label: "Backend Developer" },
  { value: "frontend-developer", label: "Frontend Developer" },
  { value: "fullstack-developer", label: "Full Stack Developer" },
  { value: "data-scientist", label: "Data Scientist" },
  { value: "ml-engineer", label: "Machine Learning Engineer" },
  { value: "software-engineer", label: "Software Engineer" },
];

export function getRoleLabel(value: string): string {
  return roles.find((role) => role.value === value)?.label ?? value;
}

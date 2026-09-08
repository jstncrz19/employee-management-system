function CreateEmployeeForm({
  form,
  submitting,
  onChange,
  onSubmit,
}) {
  return (
    <section>
      <h2>Create Employee</h2>

      <form onSubmit={onSubmit}>
        <div className="form-row">
          <div>
            <label htmlFor="employee-number">
              Employee Number
            </label>
            <input
              id="employee-number"
              name="employee_number"
              type="number"
              value={form.employee_number}
              onChange={onChange}
              required
            />
          </div>

          <div>
            <label htmlFor="date-hired">
              Date Hired
            </label>
            <input
              id="date-hired"
              name="date_hired"
              type="date"
              value={form.date_hired}
              onChange={onChange}
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div>
            <label htmlFor="first-name">
              First Name
            </label>
            <input
              id="first-name"
              name="first_name"
              value={form.first_name}
              onChange={onChange}
              required
            />
          </div>

          <div>
            <label htmlFor="last-name">
              Last Name
            </label>
            <input
              id="last-name"
              name="last_name"
              value={form.last_name}
              onChange={onChange}
              required
            />
          </div>
        </div>

        <div>
          <label htmlFor="employee-email">
            Email
          </label>
          <input
            id="employee-email"
            name="email"
            type="email"
            value={form.email}
            onChange={onChange}
            required
          />
        </div>

        <div className="form-row">
          <div>
            <label htmlFor="department">
              Department
            </label>
            <input
              id="department"
              name="department"
              value={form.department}
              onChange={onChange}
              required
            />
          </div>

          <div>
            <label htmlFor="position">
              Position
            </label>
            <input
              id="position"
              name="position"
              value={form.position}
              onChange={onChange}
              required
            />
          </div>
        </div>

        <button
          className="btn-primary"
          type="submit"
          disabled={submitting}
        >
          {submitting ? "Creating..." : "Create Employee"}
        </button>
      </form>
    </section>
  );
}

export default CreateEmployeeForm;

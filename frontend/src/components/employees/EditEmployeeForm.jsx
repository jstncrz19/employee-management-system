function EditEmployeeForm({ form, onChange, onSubmit, onCancel }) {
  return (
    <section>
      <h2>Edit Employee</h2>

      <form onSubmit={onSubmit}>
        <div className="form-row">
          <div>
            <label htmlFor="edit-first-name">
              First Name
            </label>
            <input
              id="edit-first-name"
              name="first_name"
              value={form.first_name}
              onChange={onChange}
              required
            />
          </div>

          <div>
            <label htmlFor="edit-last-name">
              Last Name
            </label>
            <input
              id="edit-last-name"
              name="last_name"
              value={form.last_name}
              onChange={onChange}
              required
            />
          </div>
        </div>

        <div>
          <label htmlFor="edit-email">
            Email
          </label>
          <input
            id="edit-email"
            name="email"
            type="email"
            value={form.email}
            onChange={onChange}
            required
          />
        </div>

        <div className="form-row">
          <div>
            <label htmlFor="edit-department">
              Department
            </label>
            <input
              id="edit-department"
              name="department"
              value={form.department}
              onChange={onChange}
              required
            />
          </div>

          <div>
            <label htmlFor="edit-position">
              Position
            </label>
            <input
              id="edit-position"
              name="position"
              value={form.position}
              onChange={onChange}
              required
            />
          </div>
        </div>

        <div>
          <label htmlFor="edit-status">
            Status
          </label>
          <select
            id="edit-status"
            name="status"
            value={form.status}
            onChange={onChange}
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="resigned">
              Resigned
            </option>
            <option value="terminated">
              Terminated
            </option>
          </select>
        </div>

        <div className="form-row">
          <button className="btn-primary" type="submit">
            Save Changes
          </button>

          <button
            className="btn-secondary"
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
}

export default EditEmployeeForm;

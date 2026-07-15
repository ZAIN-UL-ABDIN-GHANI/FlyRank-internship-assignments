/**
 * Standard success envelope used by every endpoint in this API.
 * Every successful response takes the shape:
 *   { "success": true, "message": "...", "data": {} }
 */
class ApiResponse {
  constructor(statusCode, data = {}, message = 'Success') {
    this.success = statusCode < 400;
    this.statusCode = statusCode;
    this.message = message;
    this.data = data;
  }

  send(res) {
    const { statusCode, ...body } = this;
    return res.status(statusCode).json(body);
  }
}

module.exports = ApiResponse;

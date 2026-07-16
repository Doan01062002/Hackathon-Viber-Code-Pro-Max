/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // standalone: build ra bundle tự chứa, Dockerfile chỉ copy phần cần thiết
  output: "standalone",
};

export default nextConfig;

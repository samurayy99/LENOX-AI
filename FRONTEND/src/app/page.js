import Footer from "@/components/Footer/Footer";
import Hero from "@/components/Hero/Hero";
import LenoxButton from "@/components/LenoxButton"; // Import the client component
import Navbar from "@/components/Navbar/Navbar";
import Why_Use from "@/components/Why_Use/Why_Use";

export default function Home() {
  return (
    <div className="">
      <Navbar />
      <Hero />
      <Why_Use />
      <LenoxButton />  {/* Use the client component here */}
      <Footer />
    </div>
  );
}

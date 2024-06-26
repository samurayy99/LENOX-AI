"use client";
import { UserContext } from "@/context/UserContext";
import { MenuIcon } from "@/helpers/icons";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense, useContext, useEffect, useState } from "react";
import Loader from "../Loader/Loader";

const Navbar = () => {
  const activePath = usePathname();
  const [profile, setProfile] = useState(false);
  const [open, setOpen] = useState(false);
  const { login, name, handleLogout, uid } = useContext(UserContext);
  const handleNavbarLinkClick = () => {
    setOpen(false);
  };
  const handleMenuOpen = () => {
    setOpen(!open);
  };

  const navLinks = [
    {
      name: "Home",
      path: "/",
    },
    {
      name: "Lenox Chat",
      path: "/lenox-chat",
    },
    {
      name: "Lenox AI",
      path: "http://localhost:5000",
    },
  ];

  useEffect(() => {}, [login, name, uid, handleLogout]);

  const useWindowDimensions = () => {
    const [windowDimensions, setWindowDimensions] = useState({
      width: undefined,
      height: undefined,
    });
    useEffect(() => {
      function handleResize() {
        setWindowDimensions({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      }
      handleResize();
      window.addEventListener("resize", handleResize);
      return () => window.removeEventListener("resize", handleResize);
    }, []);

    return windowDimensions;
  };

  const { width } = useWindowDimensions();

  return (
    <Suspense>
      <nav className="top-0 w-full z-10 sticky border-b border-gray-800 mx-auto bg-transparent backdrop-blur-sm">
        <div className="flex items-center justify-between p-5">
          {width > 769 ? (
            <> </>
          ) : (
            <ul
              className={`text-dimWhite text-[20px] font-medium bg-[#d1d5db] justify-center items-center absolute w-full top-[80px] z-50 py-8 pl-4 duration-500 ${
                open ? "left-0" : "left-[-100%]"
              }`}
              style={{ zIndex: "1" }}
            >
              {navLinks.map((navLink) => (
                <li className="text-start ml-[9rem] py-[20px]" key={navLink.path}>
                  <Link
                    href={navLink.path}
                    onClick={handleNavbarLinkClick}
                    className={`navLink hover:underline text-[#111827] ${
                      activePath === navLink.path || navLink.path + "/" ? "active" : ""
                    }`}
                  >
                    {navLink.name}
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <div className="item-navbar items-center gap-[16px] justify-center text-center flex md:ml-[16px]">
            <div className="md:hidden cursor-pointer" onClick={handleMenuOpen}>
              <MenuIcon className="w-6 h-6 text-white" />
            </div>
            <Link href="/" className="inline-flex h-10 items-start text-white rounded-lg font-extrabold text-[2rem]">
              Crypto
            </Link>
          </div>
          <div className="md:hidden item-navbar flex items-center">
            <div className="flex items-center">
              <div className="flex items-center gap-5 text-[1rem]">
                {(login === "" || login === undefined || login === null) && (
                  <Loader color="#ffffff" speed="0.5s" width="40px" radius="1px" />
                )}
                {login === false && (
                  <div className="flex">
                    <Link href={`/login`}>
                      <div
                        className="bg-white text-gray-900 rounded-full py-2 px-4 text-center cursor-pointer"
                        data-text="Sign In"
                      >
                        <span>Sign In</span>
                      </div>
                    </Link>
                  </div>
                )}
                {login === true && name != "" && (
                  <div className="relative group z-100 cursor-pointer">
                    <div
                      onClick={() => setProfile(!profile)}
                      className={`w-[40px] select-none h-[40px] bg-white cursor-pointer border-[1px] rounded-full flex border items-center justify-center`}
                    >
                      <span className="text-[18px] uppercase select-none cursor-pointer bg-center font-medium">
                        {name[0]}
                      </span>
                    </div>

                    <div
                      className={`absolute top-15 right-[4px] group-hover:block hover:block ease-in w-[160px] ${
                        profile ? "" : "hidden"
                      }`}
                    >
                      <div className="py-2"></div>
                      <ul className=" bg-gray-300 bg-secondary px-3 py-4 rounded font-light text-sm">
                        <Link href={`/profile/${uid}`}>
                          <li className="hover:underline text-[#cccccc] hover:text-[#ffffff] hover:bg-gray-200 px-4 py-2 rounded">
                            Your Profile
                          </li>
                        </Link>
                        <hr className="border-primary my-2" />
                        <li className="hover:bg-gray-200 hover:bg-primary text-[#cccccc] hover:text-[#ffffff] px-4 py-2 rounded">
                          <button onClick={handleLogout}>Log out</button>
                        </li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="item-navbar flex-row md:flex hidden">
            <ul className="flex items-center gap-5 text-[1rem]">
              {navLinks.map((navLink) => (
                <li key={navLink.path}>
                  <Link
                    href={navLink.path}
                    className={
                      activePath === navLink.path || activePath === navLink.path + "/"
                        ? "inline-block py-2 px-3 text-center text-white hover:text-white rounded-lg"
                        : "inline-block py-2 px-3 text-center text-[grey] hover:text-white rounded-lg"
                    }
                  >
                    {navLink.name}
                  </Link>
                </li>
              ))}
              {(login === "" || login === undefined || login === null) && (
                <Loader color="#ffffff" speed="0.5s" width="40px" radius="1px" />
              )}
              {login === false && login !== undefined && (
                <div className="flex">
                  <Link href={`/login`}>
                    <div
                      className="bg-white text-gray-900 rounded-full py-2 px-4 text-center cursor-pointer"
                      data-text="Sign In"
                    >
                      <span>Sign In</span>
                    </div>
                  </Link>
                </div>
              )}
              {login === true && name != "" && (
                <div className="relative group cursor-pointer">
                  <div
                    className={`w-[40px] select-none h-[40px] bg-white cursor-pointer border-[1px] rounded-full flex border items-center justify-center`}
                  >
                    <span className="text-[18px] uppercase select-none cursor-pointer bg-center font-medium">
                      {name[0]}
                    </span>
                  </div>

                  <div className="absolute top-15 right-[4px] hidden group-hover:block hover:block ease-in w-[160px]">
                    <div className="py-2"></div>
                    <ul className=" bg-gray-300 bg-secondary px-3 py-4 rounded font-light text-sm">
                      <Link href={`/profile/${uid}`}>
                        <li className="hover:underline text-[#cccccc] hover:text-[#ffffff] hover:bg-gray-200 px-4 py-2 rounded">
                          Your Profile
                        </li>
                      </Link>
                      <hr className="border-primary my-2" />
                      <li className="hover:bg-gray-200 hover:bg-primary text-[#cccccc] hover:text-[#ffffff] px-4 py-2 rounded">
                        <button onClick={handleLogout}>Log out</button>
                      </li>
                    </ul>
                  </div>
                </div>
              )}
            </ul>
          </div>
        </div>
      </nav>
    </Suspense>
  );
};

export default Navbar;

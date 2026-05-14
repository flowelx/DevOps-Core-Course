{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    prometheus-client
  ]);
  
  app = pkgs.stdenv.mkDerivation {
    pname = "devops-info-service";
    version = "1.0.0";
    
    src = ./.;
    
    buildInputs = [ pythonEnv ];
    
    installPhase = ''
      mkdir -p $out/bin $out/lib
      cp -r . $out/lib/
      
      cat > $out/bin/devops-info-service << EOF
      #!${pythonEnv}/bin/python
      import sys
      import os
      sys.path.insert(0, "$out/lib")
      os.chdir("$out/lib")
      from app import app
      import uvicorn
      
      if __name__ == "__main__":
          port = int(os.environ.get('PORT', 8000))
          host = os.environ.get('HOST', '0.0.0.0')
          uvicorn.run(app, host=host, port=port)
      EOF
      
      chmod +x $out/bin/devops-info-service
    '';
  };
  
  dockerImage = pkgs.dockerTools.buildLayeredImage {
    name = "devops-info-service-nix";
    tag = "1.0.0";
    
    contents = [ app pythonEnv ];
    
    config = {
      Cmd = [ "${app}/bin/devops-info-service" ];
      Env = [
        "PORT=8000"
        "HOST=0.0.0.0"
      ];
      ExposedPorts = {
        "8000/tcp" = {};
      };
    };
  };
  
in dockerImage